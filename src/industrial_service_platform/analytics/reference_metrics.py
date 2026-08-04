"""Independent Python reference calculations for warehouse KPI reconciliation."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from typing import TypeAlias

MetricValue: TypeAlias = int | float | None
Row: TypeAlias = dict[str, str]

KPI_NAMES = (
    "open_case_count",
    "critical_open_case_count",
    "response_sla_compliance_rate",
    "resolution_sla_compliance_rate",
    "mean_resolution_hours",
    "median_resolution_hours",
    "first_time_fix_rate",
    "repeat_failure_rate",
    "total_downtime_hours",
    "average_part_delivery_delay_hours",
    "total_service_cost_eur",
    "alert_to_case_conversion_rate",
)

OPEN_CASE_STATUSES = {"OPEN", "ASSIGNED", "IN_PROGRESS", "WAITING_PARTS"}
SUCCESSFUL_RESOLUTION_CODES = {
    "FIXED",
    "ADJUSTED",
    "REPLACED_COMPONENT",
    "NO_FAULT_FOUND",
}
REPEAT_ORDER_TYPES = {"CORRECTIVE_REPAIR", "EMERGENCY_REPAIR"}
UTC = timezone.utc


def read_csv_rows(path: Path) -> list[Row]:
    """Read one generated source file as dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse the generated UTC timestamp format."""
    if value is None or value.strip() == "":
        return None
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def hours_between(start: datetime, end: datetime) -> float:
    """Return exact elapsed hours."""
    return (end - start).total_seconds() / 3600.0


def safe_rate(numerator: int, denominator: int) -> float | None:
    """Return a decimal rate or None when no eligible population exists."""
    if denominator == 0:
        return None
    return numerator / denominator


def _sla_rate(
    cases: Iterable[Row],
    reporting_as_of: datetime,
    due_field: str,
    completed_field: str,
) -> float | None:
    outcomes: list[bool] = []
    for case in cases:
        if case["case_status"] == "CANCELLED":
            continue
        due_at = parse_timestamp(case.get(due_field))
        completed_at = parse_timestamp(case.get(completed_field))
        if due_at is None:
            continue
        if completed_at is not None:
            outcomes.append(completed_at <= due_at)
        elif reporting_as_of > due_at:
            outcomes.append(False)
    return safe_rate(sum(outcomes), len(outcomes))


def _first_time_fix_rate(
    cases: Iterable[Row],
    orders: Iterable[Row],
    reporting_as_of: datetime,
) -> float | None:
    orders_by_case: dict[str, list[Row]] = defaultdict(list)
    for order in orders:
        case_id = order.get("case_id", "")
        if case_id:
            orders_by_case[case_id].append(order)

    outcomes: list[bool] = []
    observation_cutoff = reporting_as_of - timedelta(days=30)

    for case in cases:
        if case["case_type"] != "TECHNICAL_FAULT" or case["case_status"] == "CANCELLED":
            continue
        completed_orders = [
            order
            for order in orders_by_case.get(case["case_id"], [])
            if order["order_status"] == "COMPLETED"
            and parse_timestamp(order.get("actual_start_at")) is not None
            and parse_timestamp(order.get("completed_at")) is not None
        ]

        def completed_order_sort_key(row: Row) -> tuple[datetime, str]:
            actual_start_at = parse_timestamp(row["actual_start_at"])
            if actual_start_at is None:
                raise RuntimeError("Completed order is missing actual_start_at")
            return actual_start_at, row["service_order_id"]

        completed_orders.sort(key=completed_order_sort_key)
        if not completed_orders:
            continue
        first_order = completed_orders[0]
        first_completed_at = parse_timestamp(first_order["completed_at"])
        assert first_completed_at is not None
        if first_completed_at > observation_cutoff:
            continue
        repeat_window_end = first_completed_at + timedelta(days=30)
        has_repeat_visit = any(
            order["order_type"] in REPEAT_ORDER_TYPES
            and (start_at := parse_timestamp(order.get("actual_start_at"))) is not None
            and first_completed_at < start_at <= repeat_window_end
            for order in orders_by_case.get(case["case_id"], [])
            if order["service_order_id"] != first_order["service_order_id"]
        )
        outcomes.append(
            first_order.get("resolution_code", "") in SUCCESSFUL_RESOLUTION_CODES
            and not has_repeat_visit
        )

    return safe_rate(sum(outcomes), len(outcomes))


def _repeat_failure_rate(
    cases: Iterable[Row],
    reporting_as_of: datetime,
) -> float | None:
    case_rows = list(cases)
    outcomes: list[bool] = []
    observation_cutoff = reporting_as_of - timedelta(days=30)

    for original in case_rows:
        resolved_at = parse_timestamp(original.get("resolved_at"))
        if (
            original["case_type"] != "TECHNICAL_FAULT"
            or original["case_status"] == "CANCELLED"
            or not original.get("asset_id")
            or not original.get("fault_category")
            or resolved_at is None
            or resolved_at > observation_cutoff
        ):
            continue
        window_end = resolved_at + timedelta(days=30)
        repeated = any(
            candidate["case_id"] != original["case_id"]
            and candidate["case_type"] == "TECHNICAL_FAULT"
            and candidate["case_status"] != "CANCELLED"
            and candidate.get("asset_id") == original["asset_id"]
            and candidate.get("fault_category") == original["fault_category"]
            and (created_at := parse_timestamp(candidate.get("created_at"))) is not None
            and resolved_at < created_at <= window_end
            for candidate in case_rows
        )
        outcomes.append(repeated)

    return safe_rate(sum(outcomes), len(outcomes))


def _total_downtime_hours(
    orders: Iterable[Row],
    reporting_as_of: datetime,
) -> float:
    intervals_by_asset: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
    for order in orders:
        if order["order_status"] == "CANCELLED":
            continue
        start_at = parse_timestamp(order.get("downtime_start_at"))
        end_at = parse_timestamp(order.get("downtime_end_at"))
        if start_at is None or end_at is None or end_at <= start_at or start_at >= reporting_as_of:
            continue
        intervals_by_asset[order["asset_id"]].append((start_at, min(end_at, reporting_as_of)))

    total = 0.0
    for intervals in intervals_by_asset.values():
        intervals.sort()
        current_start, current_end = intervals[0]
        for start_at, end_at in intervals[1:]:
            if start_at <= current_end:
                current_end = max(current_end, end_at)
            else:
                total += hours_between(current_start, current_end)
                current_start, current_end = start_at, end_at
        total += hours_between(current_start, current_end)
    return total


def compute_reference_metrics(
    source_directory: Path,
    reporting_as_of: datetime,
) -> dict[str, MetricValue]:
    """Calculate the reconciliation KPI set from generated CSV files."""
    reporting_as_of = reporting_as_of.astimezone(UTC)
    cases = read_csv_rows(source_directory / "customer_cases.csv")
    orders = read_csv_rows(source_directory / "service_orders.csv")
    part_lines = read_csv_rows(source_directory / "service_order_parts.csv")
    costs = read_csv_rows(source_directory / "service_costs.csv")
    alerts = read_csv_rows(source_directory / "equipment_alerts.csv")

    open_cases = [
        case
        for case in cases
        if case["case_status"] in OPEN_CASE_STATUSES
        and (created_at := parse_timestamp(case.get("created_at"))) is not None
        and created_at <= reporting_as_of
    ]
    resolution_hours = [
        hours_between(created_at, resolved_at)
        for case in cases
        if case["case_status"] != "CANCELLED"
        and (created_at := parse_timestamp(case.get("created_at"))) is not None
        and (resolved_at := parse_timestamp(case.get("resolved_at"))) is not None
        and resolved_at >= created_at
    ]
    delayed_part_hours = [
        delay
        for line in part_lines
        if (required_at := parse_timestamp(line.get("required_at"))) is not None
        and (delivered_at := parse_timestamp(line.get("delivered_at"))) is not None
        and (delay := max(0.0, hours_between(required_at, delivered_at))) > 0
    ]
    eligible_alerts = [
        alert
        for alert in alerts
        if (raised_at := parse_timestamp(alert.get("raised_at"))) is not None
        and raised_at <= reporting_as_of
    ]

    metrics: dict[str, MetricValue] = {
        "open_case_count": len(open_cases),
        "critical_open_case_count": sum(case["priority"] == "CRITICAL" for case in open_cases),
        "response_sla_compliance_rate": _sla_rate(
            cases,
            reporting_as_of,
            "response_due_at",
            "first_response_at",
        ),
        "resolution_sla_compliance_rate": _sla_rate(
            cases,
            reporting_as_of,
            "resolution_due_at",
            "resolved_at",
        ),
        "mean_resolution_hours": mean(resolution_hours) if resolution_hours else None,
        "median_resolution_hours": median(resolution_hours) if resolution_hours else None,
        "first_time_fix_rate": _first_time_fix_rate(cases, orders, reporting_as_of),
        "repeat_failure_rate": _repeat_failure_rate(cases, reporting_as_of),
        "total_downtime_hours": _total_downtime_hours(orders, reporting_as_of),
        "average_part_delivery_delay_hours": (
            mean(delayed_part_hours) if delayed_part_hours else None
        ),
        "total_service_cost_eur": math.fsum(
            float(cost["cost_amount_eur"]) for cost in costs if float(cost["cost_amount_eur"]) >= 0
        ),
        "alert_to_case_conversion_rate": safe_rate(
            sum(bool(alert.get("related_case_id")) for alert in eligible_alerts),
            len(eligible_alerts),
        ),
    }
    if tuple(metrics) != KPI_NAMES:
        raise RuntimeError("Reference metric order does not match KPI_NAMES")
    return metrics


def compare_metric_sets(
    reference: Mapping[str, MetricValue],
    warehouse: Mapping[str, MetricValue],
    tolerances: Mapping[str, float],
) -> list[dict[str, object]]:
    """Compare two metric sets and return one result record per KPI."""
    results: list[dict[str, object]] = []
    for name in KPI_NAMES:
        expected = reference.get(name)
        actual = warehouse.get(name)
        tolerance = float(tolerances.get(name, 0.0))
        if expected is None or actual is None:
            passed = expected is None and actual is None
            difference: float | None = None
        else:
            difference = abs(float(actual) - float(expected))
            passed = difference <= tolerance
        results.append(
            {
                "metric": name,
                "reference": expected,
                "warehouse": actual,
                "absolute_difference": difference,
                "tolerance": tolerance,
                "passed": passed,
            }
        )
    return results
