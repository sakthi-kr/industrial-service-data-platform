from __future__ import annotations

from industrial_service_platform.cli import build_parser


def test_ingestion_commands_are_registered() -> None:
    parser = build_parser()

    assert parser.parse_args(["prepare-ingestion"]).command == "prepare-ingestion"
    assert parser.parse_args(["test-snowflake"]).command == "test-snowflake"
    assert parser.parse_args(["create-raw-tables"]).command == "create-raw-tables"
    assert parser.parse_args(["ingest"]).command == "ingest"


def test_repeated_dataset_selection_is_preserved() -> None:
    parser = build_parser()
    args = parser.parse_args(["ingest", "--dataset", "customers", "--dataset", "sites"])

    assert args.datasets == ["customers", "sites"]
