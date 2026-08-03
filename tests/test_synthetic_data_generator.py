from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from industrial_service_platform.generation.config import GenerationConfig
from industrial_service_platform.generation.generator import SyntheticDataGenerator

SCHEMA_PATH = Path("config/source_schema.json")


def test_generator_creates_all_datasets_with_expected_counts(
    small_generation_config: Path,
) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    result = SyntheticDataGenerator(config, SCHEMA_PATH).generate()

    assert set(result.row_counts) == {
        "assets",
        "case_status_history",
        "customer_cases",
        "customers",
        "equipment_alerts",
        "parts",
        "service_contracts",
        "service_costs",
        "service_order_parts",
        "service_orders",
        "sites",
        "technician_notes",
        "technicians",
    }
    for dataset, expected in config.row_counts.items():
        assert result.row_counts[dataset] == expected

    assert result.row_counts["case_status_history"] >= result.row_counts["customer_cases"]
    assert result.row_counts["service_costs"] >= result.row_counts["service_orders"]

    summary = json.loads(
        (result.output_directory / "generation_summary.json").read_text(encoding="utf-8")
    )
    assert summary["quality_signals"]["invalid_example_scenarios"] == 7
    assert summary["quality_signals"]["delayed_part_lines"] > 0
    assert summary["quality_signals"]["alerts_linked_to_cases"] > 0


def test_generator_writes_small_tracked_samples(small_generation_config: Path) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    result = SyntheticDataGenerator(config, SCHEMA_PATH).generate()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    for dataset_name, dataset_spec in schema["datasets"].items():
        sample_path = result.sample_directory / dataset_spec["file_name"]
        with sample_path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == min(config.sample_rows_per_dataset, result.row_counts[dataset_name])


def test_generation_is_byte_reproducible(tmp_path: Path) -> None:
    first_config_path = _write_reproducibility_config(tmp_path, "first")
    second_config_path = _write_reproducibility_config(tmp_path, "second")

    first = SyntheticDataGenerator(
        GenerationConfig.from_json(first_config_path),
        SCHEMA_PATH,
    ).generate()
    second = SyntheticDataGenerator(
        GenerationConfig.from_json(second_config_path),
        SCHEMA_PATH,
    ).generate()

    first_hashes = _dataset_hashes(first.output_directory)
    second_hashes = _dataset_hashes(second.output_directory)
    assert first_hashes == second_hashes


def _write_reproducibility_config(tmp_path: Path, name: str) -> Path:
    config = {
        "seed": 17,
        "history_start": "2024-01-01T00:00:00Z",
        "reporting_as_of": "2026-08-01T00:00:00Z",
        "output_directory": str(tmp_path / name / "generated"),
        "sample_directory": str(tmp_path / name / "samples"),
        "sample_rows_per_dataset": 3,
        "row_counts": {
            "assets": 12,
            "customer_cases": 30,
            "customers": 5,
            "equipment_alerts": 45,
            "parts": 12,
            "service_contracts": 10,
            "service_order_parts": 40,
            "service_orders": 24,
            "sites": 8,
            "technician_notes": 20,
            "technicians": 6,
        },
    }
    path = tmp_path / f"{name}.json"
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def _dataset_hashes(directory: Path) -> dict[str, str]:
    ignored = {"generation_manifest.json"}
    return {
        path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and path.name not in ignored
    }
