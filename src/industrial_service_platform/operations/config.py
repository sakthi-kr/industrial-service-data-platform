"""Configuration for operational health checks and recovery drills."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class OperationalConfigurationError(ValueError):
    """Raised when operational-health configuration is incomplete or invalid."""


@dataclass(frozen=True)
class RelationExpectation:
    """Expected row count for one Snowflake relation."""

    relation: str
    expected_rows: int


@dataclass(frozen=True)
class OperationalConfig:
    """Validated operational thresholds and Snowflake object expectations."""

    snowflake_role: str
    output_path: Path
    recovery_output_path: Path
    required_pipeline_status: str
    max_pipeline_age_hours: float
    minimum_rows_received: int
    max_rejection_rate: float
    warehouse_name: str
    expected_warehouse_size: str
    max_auto_suspend_seconds: int
    auto_resume_required: bool
    max_failed_quality_checks: int
    max_invalid_enrichment_rows: int
    relations: tuple[RelationExpectation, ...]

    @classmethod
    def from_json(cls, path: Path) -> OperationalConfig:
        """Load and validate operational settings from JSON."""
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        pipeline = data["pipeline"]
        warehouse = data["warehouse"]
        quality = data["quality"]
        relations = tuple(
            RelationExpectation(
                relation=str(item["relation"]),
                expected_rows=int(item["expected_rows"]),
            )
            for item in data["relations"]
        )
        config = cls(
            snowflake_role=str(data["snowflake_role"]),
            output_path=Path(str(data["output_path"])),
            recovery_output_path=Path(str(data["recovery_output_path"])),
            required_pipeline_status=str(pipeline["required_status"]),
            max_pipeline_age_hours=float(pipeline["max_age_hours"]),
            minimum_rows_received=int(pipeline["minimum_rows_received"]),
            max_rejection_rate=float(pipeline["max_rejection_rate"]),
            warehouse_name=str(warehouse["name"]),
            expected_warehouse_size=str(warehouse["expected_size"]),
            max_auto_suspend_seconds=int(warehouse["max_auto_suspend_seconds"]),
            auto_resume_required=bool(warehouse["auto_resume_required"]),
            max_failed_quality_checks=int(quality["max_failed_checks"]),
            max_invalid_enrichment_rows=int(quality["max_invalid_enrichment_rows"]),
            relations=relations,
        )
        config.validate()
        return config

    def validate(self) -> None:
        """Reject unsafe or contradictory thresholds."""
        if not self.snowflake_role.strip():
            raise OperationalConfigurationError("snowflake_role cannot be empty")
        if self.max_pipeline_age_hours <= 0:
            raise OperationalConfigurationError("max_pipeline_age_hours must be positive")
        if self.minimum_rows_received < 1:
            raise OperationalConfigurationError("minimum_rows_received must be positive")
        if not 0 <= self.max_rejection_rate <= 1:
            raise OperationalConfigurationError("max_rejection_rate must be between zero and one")
        if self.max_auto_suspend_seconds < 1:
            raise OperationalConfigurationError("max_auto_suspend_seconds must be positive")
        if self.max_failed_quality_checks < 0:
            raise OperationalConfigurationError("max_failed_quality_checks cannot be negative")
        if self.max_invalid_enrichment_rows < 0:
            raise OperationalConfigurationError("max_invalid_enrichment_rows cannot be negative")
        if not self.relations:
            raise OperationalConfigurationError("at least one relation expectation is required")
        names = [item.relation for item in self.relations]
        if len(names) != len(set(names)):
            raise OperationalConfigurationError("relation expectations must be unique")
        if any(item.expected_rows < 0 for item in self.relations):
            raise OperationalConfigurationError("expected row counts cannot be negative")
