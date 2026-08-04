"""Command-line interface for the industrial service data platform."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from industrial_service_platform.generation.config import GenerationConfig
from industrial_service_platform.generation.generator import SyntheticDataGenerator
from industrial_service_platform.generation.validation import validate_directory
from industrial_service_platform.ingestion.config import IngestionSettings, SnowflakeSettings
from industrial_service_platform.ingestion.service import IngestionService, safe_connection_output


def _add_ingestion_arguments(parser: argparse.ArgumentParser, include_source: bool = True) -> None:
    parser.add_argument(
        "--ingestion-config",
        type=Path,
        default=Path("config/ingestion.json"),
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        default=None,
        help="Load one named dataset. Repeat to select several datasets.",
    )
    if include_source:
        parser.add_argument(
            "--input-directory",
            type=Path,
            default=None,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="industrial-service-data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser(
        "generate-data",
        help="Generate deterministic synthetic industrial service datasets.",
    )
    generate_parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/data_generation.json"),
    )
    generate_parser.add_argument(
        "--schema",
        type=Path,
        default=Path("config/source_schema.json"),
    )

    validate_parser = subparsers.add_parser(
        "validate-data",
        help="Validate generated CSV files against the source schema.",
    )
    validate_parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/data_generation.json"),
    )
    validate_parser.add_argument(
        "--schema",
        type=Path,
        default=Path("config/source_schema.json"),
    )
    validate_parser.add_argument(
        "--input-directory",
        type=Path,
        default=None,
    )
    validate_parser.add_argument(
        "--report",
        type=Path,
        default=None,
    )

    prepare_parser = subparsers.add_parser(
        "prepare-ingestion",
        help="Validate source files and report accepted and rejected row counts locally.",
    )
    _add_ingestion_arguments(prepare_parser)
    prepare_parser.add_argument("--report", type=Path, default=None)

    connection_parser = subparsers.add_parser(
        "test-snowflake",
        help="Test the Snowflake connector and print non-secret session context.",
    )
    _add_ingestion_arguments(connection_parser, include_source=False)

    tables_parser = subparsers.add_parser(
        "create-raw-tables",
        help="Create all configured Snowflake raw tables without loading data.",
    )
    _add_ingestion_arguments(tables_parser, include_source=False)

    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Validate CSV sources and idempotently load them into Snowflake.",
    )
    _add_ingestion_arguments(ingest_parser)
    ingest_parser.add_argument("--report", type=Path, default=None)
    return parser


def _selected_datasets(args: argparse.Namespace) -> tuple[str, ...] | None:
    values = getattr(args, "datasets", None)
    if values is None:
        return None
    return tuple(str(value) for value in values)


def _ingestion_service(args: argparse.Namespace, require_snowflake: bool) -> IngestionService:
    ingestion_settings = IngestionSettings.from_json(args.ingestion_config)
    snowflake_settings = (
        SnowflakeSettings.from_environment(args.env_file) if require_snowflake else None
    )
    return IngestionService(ingestion_settings, snowflake_settings)


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate-data":
        config = GenerationConfig.from_json(args.config)
        generation_result = SyntheticDataGenerator(config, args.schema).generate()
        print(
            "Synthetic data generation passed: "
            f"{len(generation_result.row_counts)} datasets, "
            f"{sum(generation_result.row_counts.values())} rows"
        )
        print(f"Full data: {generation_result.output_directory}")
        print(f"Tracked samples: {generation_result.sample_directory}")
        return 0

    if args.command == "validate-data":
        config = GenerationConfig.from_json(args.config)
        input_directory = args.input_directory or config.output_directory
        report = validate_directory(
            input_directory,
            args.schema,
            expected_counts=config.row_counts,
        )
        report_path = args.report or input_directory / "validation_report.json"
        report.write_json(report_path)
        _print_json(
            {
                "is_valid": report.is_valid,
                "issue_count": len(report.issues),
                "row_counts": report.row_counts,
            }
        )
        return 0 if report.is_valid else 1

    if args.command == "prepare-ingestion":
        service = _ingestion_service(args, require_snowflake=False)
        preparation_result = service.prepare(
            _selected_datasets(args),
            source_directory=args.input_directory,
        )
        report_path = service.write_preparation_report(preparation_result, args.report)
        output = preparation_result.to_dict()
        output["report"] = str(report_path)
        _print_json(output)
        return 0

    if args.command == "test-snowflake":
        service = _ingestion_service(args, require_snowflake=True)
        _print_json(safe_connection_output(service.test_connection()))
        return 0

    if args.command == "create-raw-tables":
        service = _ingestion_service(args, require_snowflake=True)
        count = service.create_raw_tables(_selected_datasets(args))
        _print_json({"created_or_verified_raw_tables": count})
        return 0

    if args.command == "ingest":
        service = _ingestion_service(args, require_snowflake=True)
        ingestion_result = service.ingest(
            _selected_datasets(args),
            source_directory=args.input_directory,
            report_path=args.report,
        )
        _print_json(ingestion_result.to_dict())
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
