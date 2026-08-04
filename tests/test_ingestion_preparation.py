from __future__ import annotations

import csv
from pathlib import Path

from industrial_service_platform.generation.config import GenerationConfig
from industrial_service_platform.generation.generator import SyntheticDataGenerator
from industrial_service_platform.ingestion.prepare import prepare_source_directory

SCHEMA_PATH = Path("config/source_schema.json")


def test_generated_sources_prepare_without_rejections(
    small_generation_config: Path,
) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    generated = SyntheticDataGenerator(config, SCHEMA_PATH).generate()

    result = prepare_source_directory(generated.output_directory, SCHEMA_PATH)

    assert result.rows_received == sum(generated.row_counts.values())
    assert result.rows_accepted == result.rows_received
    assert result.rows_rejected == 0
    assert len(result.datasets) == 13


def test_invalid_parent_record_rejects_dependent_rows(
    small_generation_config: Path,
) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    generated = SyntheticDataGenerator(config, SCHEMA_PATH).generate()
    customers_path = generated.output_directory / "customers.csv"

    with customers_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        field_names = list(rows[0])
    rows[0]["customer_status"] = "NOT_A_STATUS"
    invalid_customer_id = rows[0]["customer_id"]
    with customers_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=field_names)
        writer.writeheader()
        writer.writerows(rows)

    result = prepare_source_directory(generated.output_directory, SCHEMA_PATH)
    customers = next(item for item in result.datasets if item.definition.name == "customers")

    assert len(customers.rejected) == 1
    assert customers.rejected[0].business_identifier == invalid_customer_id
    assert any(issue.code == "INVALID_ENUM_VALUE" for issue in customers.rejected[0].issues)
    assert result.rows_rejected > 1


def test_dataset_selection_preserves_catalogue_order(
    small_generation_config: Path,
) -> None:
    config = GenerationConfig.from_json(small_generation_config)
    generated = SyntheticDataGenerator(config, SCHEMA_PATH).generate()

    result = prepare_source_directory(
        generated.output_directory,
        SCHEMA_PATH,
        selected_datasets=("sites", "customers"),
    )

    assert [dataset.definition.name for dataset in result.datasets] == ["customers", "sites"]
