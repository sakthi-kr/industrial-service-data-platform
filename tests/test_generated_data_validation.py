from __future__ import annotations

import csv
import json
from pathlib import Path

from industrial_service_platform.generation.config import GenerationConfig
from industrial_service_platform.generation.generator import SyntheticDataGenerator
from industrial_service_platform.generation.validation import (
    load_tables,
    validate_directory,
    validate_tables,
)

SCHEMA_PATH = Path("config/source_schema.json")


def test_generated_data_passes_schema_and_domain_validation(
    small_generation_config: Path,
) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    result = SyntheticDataGenerator(config, SCHEMA_PATH).generate()

    report = validate_directory(
        result.output_directory,
        SCHEMA_PATH,
        expected_counts=config.row_counts,
    )

    assert report.is_valid
    assert report.issues == ()


def test_missing_source_file_is_reported(small_generation_config: Path) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    result = SyntheticDataGenerator(config, SCHEMA_PATH).generate()
    (result.output_directory / "assets.csv").unlink()

    report = validate_directory(result.output_directory, SCHEMA_PATH)

    assert not report.is_valid
    assert any(
        issue.dataset == "assets" and issue.code == "MISSING_DATASET" for issue in report.issues
    )


def test_invalid_examples_trigger_documented_error_codes(
    small_generation_config: Path,
) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    result = SyntheticDataGenerator(config, SCHEMA_PATH).generate()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    tables = load_tables(result.output_directory, schema)

    invalid_directory = result.output_directory / "invalid"
    manifest = json.loads(
        (invalid_directory / "invalid_manifest.json").read_text(encoding="utf-8")
    )["scenarios"]

    for dataset_name, dataset_spec in schema["datasets"].items():
        invalid_path = invalid_directory / dataset_spec["file_name"]
        if not invalid_path.exists():
            continue
        with invalid_path.open("r", encoding="utf-8", newline="") as handle:
            tables[dataset_name].extend(dict(row) for row in csv.DictReader(handle))

    report = validate_tables(tables, schema)
    codes_by_dataset = {(issue.dataset, issue.code) for issue in report.issues}

    for scenario in manifest:
        assert (scenario["dataset"], scenario["expected_code"]) in codes_by_dataset
