from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from industrial_service_platform.analytics.reference_metrics import (
    compare_metric_sets,
    compute_reference_metrics,
)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_fixture(directory: Path) -> None:
    case_fields = [
        "case_id",
        "case_type",
        "case_status",
        "priority",
        "asset_id",
        "fault_category",
        "created_at",
        "response_due_at",
        "resolution_due_at",
        "first_response_at",
        "resolved_at",
    ]
    write_csv(
        directory / "customer_cases.csv",
        case_fields,
        [
            {
                "case_id": "C1",
                "case_type": "TECHNICAL_FAULT",
                "case_status": "CLOSED",
                "priority": "HIGH",
                "asset_id": "A1",
                "fault_category": "BEARING",
                "created_at": "2026-01-01T00:00:00Z",
                "response_due_at": "2026-01-01T04:00:00Z",
                "resolution_due_at": "2026-01-03T00:00:00Z",
                "first_response_at": "2026-01-01T02:00:00Z",
                "resolved_at": "2026-01-02T00:00:00Z",
            },
            {
                "case_id": "C2",
                "case_type": "TECHNICAL_FAULT",
                "case_status": "IN_PROGRESS",
                "priority": "MEDIUM",
                "asset_id": "A2",
                "fault_category": "PRESSURE",
                "created_at": "2026-01-10T00:00:00Z",
                "response_due_at": "2026-01-10T04:00:00Z",
                "resolution_due_at": "2026-01-12T00:00:00Z",
                "first_response_at": "2026-01-10T06:00:00Z",
                "resolved_at": "",
            },
            {
                "case_id": "C3",
                "case_type": "TECHNICAL_FAULT",
                "case_status": "CLOSED",
                "priority": "LOW",
                "asset_id": "A1",
                "fault_category": "BEARING",
                "created_at": "2026-01-20T00:00:00Z",
                "response_due_at": "2026-01-20T04:00:00Z",
                "resolution_due_at": "2026-02-03T00:00:00Z",
                "first_response_at": "2026-01-20T01:00:00Z",
                "resolved_at": "2026-02-01T00:00:00Z",
            },
            {
                "case_id": "C4",
                "case_type": "GENERAL_ENQUIRY",
                "case_status": "OPEN",
                "priority": "CRITICAL",
                "asset_id": "",
                "fault_category": "",
                "created_at": "2026-03-01T00:00:00Z",
                "response_due_at": "2026-03-01T04:00:00Z",
                "resolution_due_at": "2026-04-02T00:00:00Z",
                "first_response_at": "",
                "resolved_at": "",
            },
        ],
    )
    order_fields = [
        "service_order_id",
        "case_id",
        "asset_id",
        "order_type",
        "order_status",
        "actual_start_at",
        "completed_at",
        "downtime_start_at",
        "downtime_end_at",
        "resolution_code",
    ]
    write_csv(
        directory / "service_orders.csv",
        order_fields,
        [
            {
                "service_order_id": "O1",
                "case_id": "C1",
                "asset_id": "A1",
                "order_type": "CORRECTIVE_REPAIR",
                "order_status": "COMPLETED",
                "actual_start_at": "2026-01-02T00:00:00Z",
                "completed_at": "2026-01-02T02:00:00Z",
                "downtime_start_at": "2026-01-02T00:00:00Z",
                "downtime_end_at": "2026-01-02T10:00:00Z",
                "resolution_code": "FIXED",
            },
            {
                "service_order_id": "O2",
                "case_id": "C1",
                "asset_id": "A1",
                "order_type": "CORRECTIVE_REPAIR",
                "order_status": "COMPLETED",
                "actual_start_at": "2026-01-10T00:00:00Z",
                "completed_at": "2026-01-10T01:00:00Z",
                "downtime_start_at": "2026-01-02T05:00:00Z",
                "downtime_end_at": "2026-01-02T15:00:00Z",
                "resolution_code": "FIXED",
            },
            {
                "service_order_id": "O3",
                "case_id": "C3",
                "asset_id": "A1",
                "order_type": "INSPECTION",
                "order_status": "COMPLETED",
                "actual_start_at": "2026-02-01T00:00:00Z",
                "completed_at": "2026-02-01T01:00:00Z",
                "downtime_start_at": "2026-02-01T00:00:00Z",
                "downtime_end_at": "2026-02-01T02:00:00Z",
                "resolution_code": "ADJUSTED",
            },
        ],
    )
    write_csv(
        directory / "service_order_parts.csv",
        ["service_order_id", "part_id", "line_number", "required_at", "delivered_at"],
        [
            {
                "service_order_id": "O1",
                "part_id": "P1",
                "line_number": "1",
                "required_at": "2026-01-02T00:00:00Z",
                "delivered_at": "2026-01-03T00:00:00Z",
            },
            {
                "service_order_id": "O3",
                "part_id": "P2",
                "line_number": "1",
                "required_at": "2026-02-02T00:00:00Z",
                "delivered_at": "2026-02-01T00:00:00Z",
            },
        ],
    )
    write_csv(
        directory / "service_costs.csv",
        ["service_cost_id", "service_order_id", "cost_amount_eur"],
        [
            {"service_cost_id": "S1", "service_order_id": "O1", "cost_amount_eur": "100"},
            {"service_cost_id": "S2", "service_order_id": "O3", "cost_amount_eur": "50"},
        ],
    )
    write_csv(
        directory / "equipment_alerts.csv",
        ["alert_id", "related_case_id", "raised_at"],
        [
            {
                "alert_id": "A1",
                "related_case_id": "C1",
                "raised_at": "2026-01-01T00:00:00Z",
            },
            {
                "alert_id": "A2",
                "related_case_id": "",
                "raised_at": "2026-01-02T00:00:00Z",
            },
        ],
    )


def test_reference_metrics_cover_all_rules(tmp_path: Path) -> None:
    build_fixture(tmp_path)
    metrics = compute_reference_metrics(
        tmp_path,
        datetime(2026, 4, 1, tzinfo=timezone.utc),
    )
    assert metrics["open_case_count"] == 2
    assert metrics["critical_open_case_count"] == 1
    assert metrics["response_sla_compliance_rate"] == pytest.approx(0.5)
    assert metrics["resolution_sla_compliance_rate"] == pytest.approx(2 / 3)
    assert metrics["mean_resolution_hours"] == pytest.approx(156.0)
    assert metrics["median_resolution_hours"] == pytest.approx(156.0)
    assert metrics["first_time_fix_rate"] == pytest.approx(0.5)
    assert metrics["repeat_failure_rate"] == pytest.approx(0.5)
    assert metrics["total_downtime_hours"] == pytest.approx(17.0)
    assert metrics["average_part_delivery_delay_hours"] == pytest.approx(24.0)
    assert metrics["total_service_cost_eur"] == pytest.approx(150.0)
    assert metrics["alert_to_case_conversion_rate"] == pytest.approx(0.5)


def test_metric_comparison_uses_metric_specific_tolerances() -> None:
    reference = {"open_case_count": 2}
    warehouse = {"open_case_count": 2.1}
    results = compare_metric_sets(reference, warehouse, {"open_case_count": 0.2})
    open_case_result = next(item for item in results if item["metric"] == "open_case_count")
    assert open_case_result["passed"] is True
