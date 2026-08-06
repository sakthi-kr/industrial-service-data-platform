"""Deterministic recovery drills that prove health checks detect known failures."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.health import evaluate_health
from industrial_service_platform.operations.models import (
    OperationalSnapshot,
    RecoveryDrillResult,
)

UTC = timezone.utc


def healthy_snapshot(config: OperationalConfig) -> OperationalSnapshot:
    """Create a deterministic healthy baseline without contacting Snowflake."""
    observed_at = datetime(2026, 8, 6, 12, 0, tzinfo=UTC)
    return OperationalSnapshot(
        observed_at=observed_at,
        latest_run_id="RUN-HEALTHY",
        latest_run_status=config.required_pipeline_status,
        latest_run_finished_at=observed_at - timedelta(hours=1),
        latest_rows_received=config.minimum_rows_received,
        latest_rows_loaded=0,
        latest_rows_rejected=0,
        relation_counts={item.relation: item.expected_rows for item in config.relations},
        failed_quality_checks=0,
        invalid_enrichment_rows=0,
        warehouse_size=config.expected_warehouse_size,
        warehouse_auto_suspend_seconds=config.max_auto_suspend_seconds,
        warehouse_auto_resume=config.auto_resume_required,
    )


def run_recovery_drills(config: OperationalConfig) -> tuple[RecoveryDrillResult, ...]:
    """Run non-destructive scenarios and confirm each expected control fires."""
    baseline = healthy_snapshot(config)
    first_relation = config.relations[0]
    drifted_counts = dict(baseline.relation_counts)
    drifted_counts[first_relation.relation] = first_relation.expected_rows - 1

    scenarios = (
        (
            "failed_pipeline",
            replace(baseline, latest_run_status="FAILED"),
            "latest_pipeline_status",
        ),
        (
            "stale_pipeline",
            replace(
                baseline,
                latest_run_finished_at=baseline.observed_at
                - timedelta(hours=config.max_pipeline_age_hours + 1),
            ),
            "latest_pipeline_freshness",
        ),
        (
            "excessive_rejections",
            replace(
                baseline,
                latest_rows_rejected=max(
                    1,
                    int(baseline.latest_rows_received * (config.max_rejection_rate + 0.01)),
                ),
            ),
            "latest_pipeline_rejection_rate",
        ),
        (
            "relation_count_drift",
            replace(baseline, relation_counts=drifted_counts),
            f"relation_row_count:{first_relation.relation}",
        ),
        (
            "invalid_enrichment",
            replace(baseline, invalid_enrichment_rows=1),
            "note_enrichment_validity",
        ),
        (
            "warehouse_cost_misconfiguration",
            replace(
                baseline,
                warehouse_auto_suspend_seconds=(config.max_auto_suspend_seconds + 60),
            ),
            "warehouse_auto_suspend",
        ),
    )

    results: list[RecoveryDrillResult] = []
    for name, snapshot, expected_check in scenarios:
        report = evaluate_health(snapshot, config)
        failed_names = {check.name for check in report.checks if check.status == "FAIL"}
        results.append(
            RecoveryDrillResult(
                scenario=name,
                expected_failed_check=expected_check,
                detected=expected_check in failed_names,
                overall_status=report.overall_status,
            )
        )
    return tuple(results)
