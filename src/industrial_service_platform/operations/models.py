"""Data structures for operational health and recovery evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal

CheckStatus = Literal["PASS", "WARNING", "FAIL"]
Scalar = str | int | float | bool | None


@dataclass(frozen=True)
class OperationalSnapshot:
    """Observed Snowflake state used by the pure health evaluator."""

    observed_at: datetime
    latest_run_id: str
    latest_run_status: str
    latest_run_finished_at: datetime | None
    latest_rows_received: int
    latest_rows_loaded: int
    latest_rows_rejected: int
    relation_counts: dict[str, int]
    failed_quality_checks: int
    invalid_enrichment_rows: int
    warehouse_size: str
    warehouse_auto_suspend_seconds: int
    warehouse_auto_resume: bool


@dataclass(frozen=True)
class CheckResult:
    """One operational assertion and its remediation guidance."""

    name: str
    status: CheckStatus
    message: str
    actual: Scalar
    expected: Scalar
    remediation: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe check representation."""
        return asdict(self)


@dataclass(frozen=True)
class HealthReport:
    """Complete operational health evaluation."""

    generated_at: datetime
    overall_status: CheckStatus
    checks: tuple[CheckResult, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe report representation."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "overall_status": self.overall_status,
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True)
class RecoveryDrillResult:
    """Result of one deterministic failure-detection drill."""

    scenario: str
    expected_failed_check: str
    detected: bool
    overall_status: CheckStatus

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe drill result."""
        return asdict(self)
