"""Command-line interface for the industrial service data platform."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from industrial_service_platform.generation.config import GenerationConfig
from industrial_service_platform.generation.generator import SyntheticDataGenerator
from industrial_service_platform.generation.validation import validate_directory


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate-data":
        config = GenerationConfig.from_json(args.config)
        result = SyntheticDataGenerator(config, args.schema).generate()
        print(
            "Synthetic data generation passed: "
            f"{len(result.row_counts)} datasets, "
            f"{sum(result.row_counts.values())} rows"
        )
        print(f"Full data: {result.output_directory}")
        print(f"Tracked samples: {result.sample_directory}")
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
        print(
            json.dumps(
                {
                    "is_valid": report.is_valid,
                    "issue_count": len(report.issues),
                    "row_counts": report.row_counts,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if report.is_valid else 1

    parser.error(f"Unsupported command: {args.command}")
    return 2
