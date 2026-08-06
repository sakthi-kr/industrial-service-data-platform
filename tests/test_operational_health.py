from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.drills import healthy_snapshot
from industrial_service_platform.operations.health import evaluate_health


def _config() -> OperationalConfig:
    return OperationalConfig.from_json(Path("config/operational_health.json"))


def test_healthy_snapshot_passes_every_check() -> None:
    config = _config()
    report = evaluate_health(healthy_snapshot(config), config)

    assert report.overall_status == "PASS"
    assert report.checks
    assert all(check.status == "PASS" for check in report.checks)


def test_stale_pipeline_is_detected() -> None:
    config = _config()
    snapshot = healthy_snapshot(config)
    stale = replace(
        snapshot,
        latest_run_finished_at=snapshot.observed_at
        - timedelta(hours=config.max_pipeline_age_hours + 1),
    )

    report = evaluate_health(stale, config)
    failed = {check.name for check in report.checks if check.status == "FAIL"}

    assert report.overall_status == "FAIL"
    assert "latest_pipeline_freshness" in failed


def test_relation_count_drift_is_detected() -> None:
    config = _config()
    snapshot = healthy_snapshot(config)
    expectation = config.relations[0]
    counts = dict(snapshot.relation_counts)
    counts[expectation.relation] -= 1

    report = evaluate_health(replace(snapshot, relation_counts=counts), config)
    failed = {check.name for check in report.checks if check.status == "FAIL"}

    assert f"relation_row_count:{expectation.relation}" in failed
