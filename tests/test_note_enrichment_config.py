import json
from pathlib import Path

import pytest

from industrial_service_platform.enrichment.config import EnrichmentConfig


def test_enrichment_config_loads(tmp_path: Path) -> None:
    values = {
        "source_directory": "data/generated",
        "output_directory": "data/generated/note_enrichment",
        "model_path": "data/generated/note_enrichment/model.joblib",
        "evaluation_path": "data/generated/note_enrichment/evaluation.json",
        "predictions_path": "data/generated/note_enrichment/predictions.csv",
        "labeled_dataset_path": "data/generated/note_enrichment/labeled.csv",
        "public_sample_directory": "data/samples/note_enrichment",
        "model_version": "test-v1",
        "random_seed": 7,
        "test_size": 0.2,
        "max_features": 1000,
        "minimum_metrics": {
            "fault_macro_f1": 0.5,
            "priority_macro_f1": 0.5,
            "component_accuracy": 0.5,
            "structured_output_validity_rate": 1.0,
        },
        "snowflake_role": "ISP_TRANSFORMER",
        "snowflake_database": "INDUSTRIAL_SERVICE_DB",
        "snowflake_schema": "STAGING",
        "snowflake_table": "NOTE_ENRICHMENT_RESULTS",
        "batch_size": 100,
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(values), encoding="utf-8")
    config = EnrichmentConfig.from_json(path)
    assert config.model_version == "test-v1"
    assert config.minimum_metrics.structured_output_validity_rate == 1.0


def test_enrichment_config_rejects_unsafe_identifier(tmp_path: Path) -> None:
    source = json.loads(Path("config/note_enrichment.json").read_text(encoding="utf-8"))
    source["snowflake_table"] = "unsafe;drop"
    path = tmp_path / "config.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="Unsafe Snowflake identifier"):
        EnrichmentConfig.from_json(path)
