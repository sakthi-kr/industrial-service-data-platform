"""Pure operational-health evaluation with explicit recovery guidance."""

from __future__ import annotations

from datetime import timezone

from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.models import (
    CheckResult,
    CheckStatus,
    HealthReport,
    OperationalSnapshot,
)

UTC = timezone.utc


def _result(
    name: str,
    passed: bool,
    message: str,
    actual: str | int | float | bool | None,
    expected: str | int | float | bool | None,
    remediation: str,
) -> CheckResult:
    return CheckResult(
        name=name,
        status="PASS" if passed else "FAIL",
        message=message,
        actual=actual,
        expected=expected,
        remediation=remediation,
    )


def _overall_status(checks: list[CheckResult]) -> CheckStatus:
    if any(check.status == "FAIL" for check in checks):
        return "FAIL"
    if any(check.status == "WARNING" for check in checks):
        return "WARNING"
    return "PASS"


def evaluate_health(
    snapshot: OperationalSnapshot,
    config: OperationalConfig,
) -> HealthReport:
    """Evaluate a collected snapshot without performing network or file I/O."""
    checks: list[CheckResult] = []
    checks.append(
        _result(
            "latest_pipeline_status",
            snapshot.latest_run_status == config.required_pipeline_status,
            "Latest ingestion pipeline run reached the required terminal status.",
            snapshot.latest_run_status,
            config.required_pipeline_status,
            "Review the latest pipeline error, correct the source or connection issue, and rerun.",
        )
    )

    if snapshot.latest_run_finished_at is None:
        age_hours: float | None = None
        fresh = False
    else:
        finished_at = snapshot.latest_run_finished_at
        if finished_at.tzinfo is None:
            finished_at = finished_at.replace(tzinfo=UTC)
        age_hours = max(
            0.0,
            (snapshot.observed_at - finished_at).total_seconds() / 3600,
        )
        fresh = age_hours <= config.max_pipeline_age_hours

    checks.append(
        _result(
            "latest_pipeline_freshness",
            fresh,
            "Latest completed ingestion run is within the configured freshness window.",
            None if age_hours is None else round(age_hours, 6),
            config.max_pipeline_age_hours,
            "Run the ingestion pipeline and investigate why scheduled or manual loading stopped.",
        )
    )
    checks.append(
        _result(
            "latest_pipeline_volume",
            snapshot.latest_rows_received >= config.minimum_rows_received,
            "Latest ingestion run received the minimum expected source volume.",
            snapshot.latest_rows_received,
            config.minimum_rows_received,
            "Regenerate or restore missing source files before rerunning ingestion.",
        )
    )

    rejection_rate = (
        snapshot.latest_rows_rejected / snapshot.latest_rows_received
        if snapshot.latest_rows_received
        else 1.0
    )
    checks.append(
        _result(
            "latest_pipeline_rejection_rate",
            rejection_rate <= config.max_rejection_rate,
            "Rejected rows remain below the configured operational threshold.",
            round(rejection_rate, 8),
            config.max_rejection_rate,
            "Inspect OPERATIONS.REJECTED_RECORDS and correct the affected source records.",
        )
    )

    checks.append(
        _result(
            "warehouse_size",
            snapshot.warehouse_size.casefold() == config.expected_warehouse_size.casefold(),
            "Warehouse size matches the cost-control configuration.",
            snapshot.warehouse_size,
            config.expected_warehouse_size,
            "Resize INDUSTRIAL_SERVICE_WH to X-Small unless a documented test requires otherwise.",
        )
    )
    checks.append(
        _result(
            "warehouse_auto_suspend",
            snapshot.warehouse_auto_suspend_seconds <= config.max_auto_suspend_seconds,
            "Warehouse auto-suspend remains within the cost-control limit.",
            snapshot.warehouse_auto_suspend_seconds,
            config.max_auto_suspend_seconds,
            "Set AUTO_SUSPEND to 60 seconds and keep AUTO_RESUME enabled.",
        )
    )
    checks.append(
        _result(
            "warehouse_auto_resume",
            snapshot.warehouse_auto_resume == config.auto_resume_required,
            "Warehouse auto-resume matches the expected setting.",
            snapshot.warehouse_auto_resume,
            config.auto_resume_required,
            "Enable AUTO_RESUME so verified jobs can start without manual warehouse changes.",
        )
    )

    for expectation in config.relations:
        actual = snapshot.relation_counts.get(expectation.relation)
        checks.append(
            _result(
                f"relation_row_count:{expectation.relation}",
                actual == expectation.expected_rows,
                "Snowflake relation row count matches the verified project baseline.",
                actual,
                expectation.expected_rows,
                "Trace the relation to its source load or dbt dependency and rebuild it.",
            )
        )

    checks.append(
        _result(
            "data_quality_failures",
            snapshot.failed_quality_checks <= config.max_failed_quality_checks,
            "No unresolved failed data-quality checks are recorded.",
            snapshot.failed_quality_checks,
            config.max_failed_quality_checks,
            "Inspect OPERATIONS.DATA_QUALITY_RESULTS and rerun the failed validation.",
        )
    )
    checks.append(
        _result(
            "note_enrichment_validity",
            snapshot.invalid_enrichment_rows <= config.max_invalid_enrichment_rows,
            "Published technician-note outputs satisfy the structured-output contract.",
            snapshot.invalid_enrichment_rows,
            config.max_invalid_enrichment_rows,
            "Republish validated predictions and rebuild the enrichment mart.",
        )
    )

    return HealthReport(
        generated_at=snapshot.observed_at,
        overall_status=_overall_status(checks),
        checks=tuple(checks),
    )
