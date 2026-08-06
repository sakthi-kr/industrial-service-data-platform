"""Configuration for technician-note enrichment."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MetricThresholds:
    """Minimum accepted evaluation metrics."""

    fault_macro_f1: float
    priority_macro_f1: float
    component_accuracy: float
    structured_output_validity_rate: float

    @classmethod
    def from_mapping(cls, values: dict[str, Any]) -> MetricThresholds:
        required = {
            "fault_macro_f1",
            "priority_macro_f1",
            "component_accuracy",
            "structured_output_validity_rate",
        }
        missing = sorted(required - values.keys())
        if missing:
            raise ValueError(f"Missing note-enrichment metric thresholds: {missing}")
        parsed = cls(**{name: float(values[name]) for name in required})
        for name, value in parsed.as_dict().items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"Metric threshold must be between zero and one: {name}")
        return parsed

    def as_dict(self) -> dict[str, float]:
        """Return a JSON-ready threshold mapping."""
        return {
            "fault_macro_f1": self.fault_macro_f1,
            "priority_macro_f1": self.priority_macro_f1,
            "component_accuracy": self.component_accuracy,
            "structured_output_validity_rate": self.structured_output_validity_rate,
        }


@dataclass(frozen=True)
class EnrichmentConfig:
    """Tracked settings for model training, evaluation, and publication."""

    source_directory: Path
    output_directory: Path
    model_path: Path
    evaluation_path: Path
    predictions_path: Path
    labeled_dataset_path: Path
    public_sample_directory: Path
    model_version: str
    random_seed: int
    test_size: float
    max_features: int
    minimum_metrics: MetricThresholds
    snowflake_role: str
    snowflake_database: str
    snowflake_schema: str
    snowflake_table: str
    batch_size: int

    @classmethod
    def from_json(cls, path: Path) -> EnrichmentConfig:
        """Load and validate the tracked JSON configuration."""
        values = json.loads(path.read_text(encoding="utf-8"))
        thresholds = MetricThresholds.from_mapping(values.pop("minimum_metrics"))
        path_fields = {
            "source_directory",
            "output_directory",
            "model_path",
            "evaluation_path",
            "predictions_path",
            "labeled_dataset_path",
            "public_sample_directory",
        }
        for name in path_fields:
            values[name] = Path(str(values[name]))
        config = cls(minimum_metrics=thresholds, **values)
        config.validate()
        return config

    def validate(self) -> None:
        """Reject unsafe or internally inconsistent settings."""
        if not self.model_version.strip():
            raise ValueError("model_version cannot be empty")
        if not 0.05 <= self.test_size <= 0.5:
            raise ValueError("test_size must be between 0.05 and 0.5")
        if self.max_features < 100:
            raise ValueError("max_features must be at least 100")
        if self.batch_size < 1:
            raise ValueError("batch_size must be positive")
        for name in (
            self.snowflake_role,
            self.snowflake_database,
            self.snowflake_schema,
            self.snowflake_table,
        ):
            if not name or not name.replace("_", "").isalnum():
                raise ValueError(f"Unsafe Snowflake identifier: {name!r}")
