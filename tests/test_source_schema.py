import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "source_schema.json"

EXPECTED_DATASETS = {
    "customers",
    "sites",
    "assets",
    "service_contracts",
    "customer_cases",
    "case_status_history",
    "service_orders",
    "technicians",
    "parts",
    "service_order_parts",
    "service_costs",
    "equipment_alerts",
    "technician_notes",
}


def load_catalogue() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_catalogue_contains_expected_datasets() -> None:
    catalogue = load_catalogue()

    assert catalogue["schema_version"] == "1.0.0"
    assert set(catalogue["datasets"]) == EXPECTED_DATASETS
    assert len(catalogue["relationships"]) == 19


def test_business_keys_exist_and_are_not_nullable() -> None:
    datasets = load_catalogue()["datasets"]

    for dataset_name, dataset in datasets.items():
        fields = {item["name"]: item for item in dataset["fields"]}

        assert len(fields) == len(dataset["fields"])
        for key_field in dataset["business_key"]:
            assert key_field in fields, f"Missing business key field: {dataset_name}.{key_field}"
            assert fields[key_field]["nullable"] is False


def test_foreign_key_references_resolve() -> None:
    datasets = load_catalogue()["datasets"]

    for dataset_name, dataset in datasets.items():
        for field in dataset["fields"]:
            reference = field.get("references")
            if reference is None:
                continue

            parent_dataset, parent_field = reference.split(".", maxsplit=1)
            assert parent_dataset in datasets, (
                f"Unknown parent dataset for {dataset_name}.{field['name']}"
            )

            parent_fields = {item["name"] for item in datasets[parent_dataset]["fields"]}
            assert parent_field in parent_fields, (
                f"Unknown parent field for {dataset_name}.{field['name']}"
            )


def test_generated_phase_one_documents_exist() -> None:
    expected_documents = [
        ROOT / "docs" / "data_dictionary.md",
        ROOT / "docs" / "entity_relationship_diagram.md",
        ROOT / "docs" / "data_model_summary.md",
    ]

    for path in expected_documents:
        text = path.read_text(encoding="utf-8")
        assert text.endswith("\n")
        assert not any(line.endswith((" ", "\t")) for line in text.splitlines())
