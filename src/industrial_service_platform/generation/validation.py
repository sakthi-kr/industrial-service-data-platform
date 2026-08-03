"""Schema, relationship, and domain validation for generated source data."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

Row = dict[str, str]
Tables = dict[str, list[Row]]


@dataclass(frozen=True)
class ValidationIssue:
    """One validation problem found in a source record."""

    dataset: str
    row_number: int
    field: str
    code: str
    message: str
    business_key: str


@dataclass(frozen=True)
class ValidationReport:
    """Validation result for a complete set of source datasets."""

    row_counts: dict[str, int]
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "row_counts": dict(sorted(self.row_counts.items())),
            "issue_count": len(self.issues),
            "issues": [asdict(issue) for issue in self.issues],
        }

    def write_json(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def load_tables(input_directory: Path, schema: dict[str, Any]) -> Tables:
    """Read all configured CSV datasets from a directory."""
    tables: Tables = {}
    for dataset_name, dataset_spec in schema["datasets"].items():
        file_path = input_directory / dataset_spec["file_name"]
        if not file_path.exists():
            tables[dataset_name] = []
            continue
        with file_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            tables[dataset_name] = [dict(row) for row in reader]
    return tables


def validate_directory(
    input_directory: Path,
    schema_path: Path,
    expected_counts: dict[str, int] | None = None,
) -> ValidationReport:
    """Validate CSV files in a directory against the schema catalogue."""
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    tables = load_tables(input_directory, schema)
    report = validate_tables(tables, schema, expected_counts=expected_counts)
    missing_issues = tuple(
        ValidationIssue(
            dataset=dataset_name,
            row_number=0,
            field="",
            code="MISSING_DATASET",
            message=f"Expected source file {dataset_spec['file_name']} is missing.",
            business_key="",
        )
        for dataset_name, dataset_spec in schema["datasets"].items()
        if not (input_directory / dataset_spec["file_name"]).exists()
    )
    return ValidationReport(
        row_counts=report.row_counts,
        issues=tuple(sorted((*report.issues, *missing_issues), key=_issue_sort_key)),
    )


def validate_tables(
    tables: Tables,
    schema: dict[str, Any],
    expected_counts: dict[str, int] | None = None,
) -> ValidationReport:
    """Validate in-memory source tables."""
    issues: list[ValidationIssue] = []
    row_counts = {name: len(rows) for name, rows in tables.items()}

    _validate_presence_and_counts(tables, schema, expected_counts, issues)
    _validate_fields_and_keys(tables, schema, issues)
    _validate_references(tables, schema, issues)
    _validate_domain_rules(tables, issues)

    return ValidationReport(
        row_counts=row_counts,
        issues=tuple(sorted(issues, key=_issue_sort_key)),
    )


def _validate_presence_and_counts(
    tables: Tables,
    schema: dict[str, Any],
    expected_counts: dict[str, int] | None,
    issues: list[ValidationIssue],
) -> None:
    for dataset_name in schema["datasets"]:
        if dataset_name not in tables:
            issues.append(
                ValidationIssue(
                    dataset=dataset_name,
                    row_number=0,
                    field="",
                    code="MISSING_DATASET",
                    message="Dataset is missing from the supplied table collection.",
                    business_key="",
                )
            )

    if expected_counts is None:
        return

    for dataset_name, expected in expected_counts.items():
        actual = len(tables.get(dataset_name, []))
        if actual != expected:
            issues.append(
                ValidationIssue(
                    dataset=dataset_name,
                    row_number=0,
                    field="",
                    code="UNEXPECTED_ROW_COUNT",
                    message=f"Expected {expected} rows but found {actual}.",
                    business_key="",
                )
            )


def _validate_fields_and_keys(
    tables: Tables,
    schema: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    for dataset_name, dataset_spec in schema["datasets"].items():
        fields = dataset_spec["fields"]
        expected_names = [field["name"] for field in fields]
        business_key_fields = dataset_spec["business_key"]
        seen_keys: dict[tuple[str, ...], int] = {}

        for row_number, row in enumerate(tables.get(dataset_name, []), start=2):
            missing_columns = [name for name in expected_names if name not in row]
            extra_columns = sorted(set(row) - set(expected_names))
            business_key = _business_key(row, business_key_fields)

            for name in missing_columns:
                issues.append(
                    _issue(
                        dataset_name,
                        row_number,
                        name,
                        "MISSING_COLUMN",
                        f"Expected column {name} is absent.",
                        business_key,
                    )
                )
            for name in extra_columns:
                issues.append(
                    _issue(
                        dataset_name,
                        row_number,
                        name,
                        "UNEXPECTED_COLUMN",
                        f"Column {name} is not defined in the source schema.",
                        business_key,
                    )
                )

            for field in fields:
                name = field["name"]
                value = row.get(name, "")
                if not field["nullable"] and value == "":
                    issues.append(
                        _issue(
                            dataset_name,
                            row_number,
                            name,
                            "MISSING_REQUIRED_FIELD",
                            f"Required field {name} is empty.",
                            business_key,
                        )
                    )
                    continue
                if value == "":
                    continue

                allowed_values = field.get("allowed_values")
                if allowed_values is not None and value not in allowed_values:
                    issues.append(
                        _issue(
                            dataset_name,
                            row_number,
                            name,
                            "INVALID_ENUM_VALUE",
                            f"Value {value!r} is not allowed for {name}.",
                            business_key,
                        )
                    )

                if not _value_matches_type(value, field["type"]):
                    issues.append(
                        _issue(
                            dataset_name,
                            row_number,
                            name,
                            "INVALID_DATA_TYPE",
                            f"Value {value!r} does not match type {field['type']}.",
                            business_key,
                        )
                    )

            key_tuple = tuple(row.get(field, "") for field in business_key_fields)
            if all(key_tuple):
                previous_row = seen_keys.get(key_tuple)
                if previous_row is not None:
                    issues.append(
                        _issue(
                            dataset_name,
                            row_number,
                            ",".join(business_key_fields),
                            "DUPLICATE_BUSINESS_KEY",
                            f"Business key duplicates row {previous_row}.",
                            business_key,
                        )
                    )
                else:
                    seen_keys[key_tuple] = row_number


def _validate_references(
    tables: Tables,
    schema: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    reference_values: dict[str, set[str]] = {}
    for dataset_name, dataset_spec in schema["datasets"].items():
        for field in dataset_spec["fields"]:
            reference_key = f"{dataset_name}.{field['name']}"
            reference_values[reference_key] = {
                row.get(field["name"], "")
                for row in tables.get(dataset_name, [])
                if row.get(field["name"], "") != ""
            }

    for dataset_name, dataset_spec in schema["datasets"].items():
        key_fields = dataset_spec["business_key"]
        for row_number, row in enumerate(tables.get(dataset_name, []), start=2):
            business_key = _business_key(row, key_fields)
            for field in dataset_spec["fields"]:
                reference = field.get("references")
                value = row.get(field["name"], "")
                if reference is None or value == "":
                    continue
                if value not in reference_values.get(reference, set()):
                    issues.append(
                        _issue(
                            dataset_name,
                            row_number,
                            field["name"],
                            "UNKNOWN_FOREIGN_KEY",
                            f"Value {value!r} does not exist in {reference}.",
                            business_key,
                        )
                    )


def _validate_domain_rules(tables: Tables, issues: list[ValidationIssue]) -> None:
    customers = _index(tables.get("customers", []), "customer_id")
    sites = _index(tables.get("sites", []), "site_id")
    assets = _index(tables.get("assets", []), "asset_id")
    contracts = _index(tables.get("service_contracts", []), "contract_id")
    cases = _index(tables.get("customer_cases", []), "case_id")
    orders = _index(tables.get("service_orders", []), "service_order_id")

    _validate_updated_timestamps(tables, issues)
    _validate_sites(tables.get("sites", []), customers, issues)
    _validate_assets(tables.get("assets", []), sites, issues)
    _validate_contracts(tables.get("service_contracts", []), sites, issues)
    _validate_cases(tables.get("customer_cases", []), sites, assets, contracts, issues)
    _validate_case_history(tables.get("case_status_history", []), cases, issues)
    _validate_orders(tables.get("service_orders", []), cases, assets, issues)
    _validate_parts(tables.get("parts", []), issues)
    _validate_order_parts(tables.get("service_order_parts", []), issues)
    _validate_costs(tables.get("service_costs", []), issues)
    _validate_alerts(tables.get("equipment_alerts", []), cases, assets, issues)
    _validate_notes(tables.get("technician_notes", []), orders, issues)


def _validate_updated_timestamps(tables: Tables, issues: list[ValidationIssue]) -> None:
    timestamped_datasets = (
        "customers",
        "sites",
        "assets",
        "service_contracts",
        "technicians",
        "parts",
    )
    for dataset_name in timestamped_datasets:
        rows = tables.get(dataset_name, [])
        for row_number, row in enumerate(rows, start=2):
            created = _parse_datetime_or_none(row.get("created_at", ""))
            updated = _parse_datetime_or_none(row.get("updated_at", ""))
            if created is not None and updated is not None and updated < created:
                issues.append(
                    _domain_issue(
                        dataset_name,
                        row_number,
                        row,
                        "updated_at",
                        "INVALID_TIMESTAMP_ORDER",
                        "updated_at precedes created_at.",
                    )
                )


def _validate_sites(
    rows: list[Row],
    customers: dict[str, Row],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        customer = customers.get(row.get("customer_id", ""))
        if customer is None:
            continue
        site_created = _parse_datetime_or_none(row.get("created_at", ""))
        customer_created = _parse_datetime_or_none(customer.get("created_at", ""))
        if (
            site_created is not None
            and customer_created is not None
            and site_created < customer_created
        ):
            issues.append(
                _domain_issue(
                    "sites",
                    row_number,
                    row,
                    "created_at",
                    "INVALID_TIMESTAMP_ORDER",
                    "Site creation precedes customer creation.",
                )
            )


def _validate_assets(rows: list[Row], sites: dict[str, Row], issues: list[ValidationIssue]) -> None:
    serial_numbers: dict[str, int] = {}
    for row_number, row in enumerate(rows, start=2):
        installation = _parse_date_or_none(row.get("installation_date", ""))
        created = _parse_datetime_or_none(row.get("created_at", ""))
        if installation is not None and created is not None and installation > created.date():
            issues.append(
                _domain_issue(
                    "assets",
                    row_number,
                    row,
                    "installation_date",
                    "INVALID_TIMESTAMP_ORDER",
                    "Asset installation date is after source record creation.",
                )
            )
        site = sites.get(row.get("site_id", ""))
        if site is None:
            continue
        serial = row.get("serial_number", "")
        if serial and row.get("asset_status") == "ACTIVE":
            previous = serial_numbers.get(serial)
            if previous is not None:
                issues.append(
                    _domain_issue(
                        "assets",
                        row_number,
                        row,
                        "serial_number",
                        "DUPLICATE_ACTIVE_SERIAL_NUMBER",
                        f"Active serial number duplicates row {previous}.",
                    )
                )
            else:
                serial_numbers[serial] = row_number


def _validate_contracts(
    rows: list[Row],
    sites: dict[str, Row],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        start = _parse_date_or_none(row.get("start_date", ""))
        end = _parse_date_or_none(row.get("end_date", ""))
        if start is not None and end is not None and end <= start:
            issues.append(
                _domain_issue(
                    "service_contracts",
                    row_number,
                    row,
                    "end_date",
                    "INVALID_TIMESTAMP_ORDER",
                    "Contract end date must be after start date.",
                )
            )
        for field in ("response_sla_hours", "resolution_sla_hours"):
            value = _parse_int_or_none(row.get(field, ""))
            if value is not None and value <= 0:
                issues.append(
                    _domain_issue(
                        "service_contracts",
                        row_number,
                        row,
                        field,
                        "INVALID_NUMERIC_VALUE",
                        f"{field} must be positive.",
                    )
                )
        site = sites.get(row.get("site_id", ""))
        if site is not None and site.get("customer_id") != row.get("customer_id"):
            issues.append(
                _domain_issue(
                    "service_contracts",
                    row_number,
                    row,
                    "customer_id",
                    "INCONSISTENT_RELATIONSHIP",
                    "Contract customer does not own the referenced site.",
                )
            )


def _validate_cases(
    rows: list[Row],
    sites: dict[str, Row],
    assets: dict[str, Row],
    contracts: dict[str, Row],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        created = _parse_datetime_or_none(row.get("created_at", ""))
        response_due = _parse_datetime_or_none(row.get("response_due_at", ""))
        resolution_due = _parse_datetime_or_none(row.get("resolution_due_at", ""))
        first_response = _parse_datetime_or_none(row.get("first_response_at", ""))
        resolved = _parse_datetime_or_none(row.get("resolved_at", ""))
        closed = _parse_datetime_or_none(row.get("closed_at", ""))
        updated = _parse_datetime_or_none(row.get("updated_at", ""))

        timestamp_pairs = [
            (created, response_due, "response_due_at", "Response deadline precedes case creation."),
            (
                created,
                resolution_due,
                "resolution_due_at",
                "Resolution deadline precedes case creation.",
            ),
            (
                created,
                first_response,
                "first_response_at",
                "First response precedes case creation.",
            ),
            (created, resolved, "resolved_at", "Resolution precedes case creation."),
            (resolved, closed, "closed_at", "Case closure precedes resolution."),
            (created, updated, "updated_at", "Case update precedes case creation."),
        ]
        for earlier, later, field, message in timestamp_pairs:
            if earlier is not None and later is not None and later < earlier:
                issues.append(
                    _domain_issue(
                        "customer_cases",
                        row_number,
                        row,
                        field,
                        "INVALID_TIMESTAMP_ORDER",
                        message,
                    )
                )

        status = row.get("case_status")
        if status in {"RESOLVED", "CLOSED"} and resolved is None:
            issues.append(
                _domain_issue(
                    "customer_cases",
                    row_number,
                    row,
                    "resolved_at",
                    "MISSING_REQUIRED_FIELD",
                    "Resolved or closed case requires resolved_at.",
                )
            )
        if status == "CLOSED" and closed is None:
            issues.append(
                _domain_issue(
                    "customer_cases",
                    row_number,
                    row,
                    "closed_at",
                    "MISSING_REQUIRED_FIELD",
                    "Closed case requires closed_at.",
                )
            )

        site = sites.get(row.get("site_id", ""))
        if site is not None and site.get("customer_id") != row.get("customer_id"):
            issues.append(
                _domain_issue(
                    "customer_cases",
                    row_number,
                    row,
                    "customer_id",
                    "INCONSISTENT_RELATIONSHIP",
                    "Case customer does not own the referenced site.",
                )
            )

        asset_id = row.get("asset_id", "")
        asset = assets.get(asset_id) if asset_id else None
        if asset is not None and asset.get("site_id") != row.get("site_id"):
            issues.append(
                _domain_issue(
                    "customer_cases",
                    row_number,
                    row,
                    "asset_id",
                    "INCONSISTENT_RELATIONSHIP",
                    "Case asset is not installed at the referenced site.",
                )
            )

        contract_id = row.get("contract_id", "")
        contract = contracts.get(contract_id) if contract_id else None
        if contract is not None and (
            contract.get("site_id") != row.get("site_id")
            or contract.get("customer_id") != row.get("customer_id")
        ):
            issues.append(
                _domain_issue(
                    "customer_cases",
                    row_number,
                    row,
                    "contract_id",
                    "INCONSISTENT_RELATIONSHIP",
                    "Case contract does not cover the referenced customer and site.",
                )
            )


def _validate_case_history(
    rows: list[Row],
    cases: dict[str, Row],
    issues: list[ValidationIssue],
) -> None:
    events_by_case: dict[str, list[tuple[int, Row]]] = {}
    for row_number, row in enumerate(rows, start=2):
        events_by_case.setdefault(row.get("case_id", ""), []).append((row_number, row))
        case = cases.get(row.get("case_id", ""))
        changed = _parse_datetime_or_none(row.get("changed_at", ""))
        case_created = _parse_datetime_or_none(case.get("created_at", "")) if case else None
        if changed is not None and case_created is not None and changed < case_created:
            issues.append(
                _domain_issue(
                    "case_status_history",
                    row_number,
                    row,
                    "changed_at",
                    "INVALID_TIMESTAMP_ORDER",
                    "Status event precedes case creation.",
                )
            )

    for case_id, events in events_by_case.items():
        ordered = sorted(events, key=lambda item: item[1].get("changed_at", ""))
        if not ordered:
            continue
        row_number, first = ordered[0]
        if first.get("previous_status", "") != "" or first.get("new_status") != "OPEN":
            issues.append(
                _domain_issue(
                    "case_status_history",
                    row_number,
                    first,
                    "new_status",
                    "INVALID_STATUS_TRANSITION",
                    f"First event for {case_id} must create OPEN status.",
                )
            )


def _validate_orders(
    rows: list[Row],
    cases: dict[str, Row],
    assets: dict[str, Row],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        created = _parse_datetime_or_none(row.get("created_at", ""))
        scheduled = _parse_datetime_or_none(row.get("scheduled_start_at", ""))
        actual = _parse_datetime_or_none(row.get("actual_start_at", ""))
        completed = _parse_datetime_or_none(row.get("completed_at", ""))
        downtime_start = _parse_datetime_or_none(row.get("downtime_start_at", ""))
        downtime_end = _parse_datetime_or_none(row.get("downtime_end_at", ""))

        checks = [
            (created, scheduled, "scheduled_start_at", "Scheduled start precedes order creation."),
            (created, actual, "actual_start_at", "Actual start precedes order creation."),
            (actual, completed, "completed_at", "Completion precedes actual start."),
            (
                downtime_start,
                downtime_end,
                "downtime_end_at",
                "Downtime end precedes downtime start.",
            ),
        ]
        for earlier, later, field, message in checks:
            if earlier is not None and later is not None and later < earlier:
                issues.append(
                    _domain_issue(
                        "service_orders",
                        row_number,
                        row,
                        field,
                        "INVALID_TIMESTAMP_ORDER",
                        message,
                    )
                )

        if row.get("order_status") == "COMPLETED" and (actual is None or completed is None):
            issues.append(
                _domain_issue(
                    "service_orders",
                    row_number,
                    row,
                    "completed_at",
                    "MISSING_REQUIRED_FIELD",
                    "Completed order requires actual_start_at and completed_at.",
                )
            )

        case_id = row.get("case_id", "")
        case = cases.get(case_id) if case_id else None
        asset = assets.get(row.get("asset_id", ""))
        if case is not None and case.get("asset_id") not in {"", row.get("asset_id")}:
            issues.append(
                _domain_issue(
                    "service_orders",
                    row_number,
                    row,
                    "asset_id",
                    "INCONSISTENT_RELATIONSHIP",
                    "Service order asset differs from the linked case asset.",
                )
            )
        if asset is None:
            continue


def _validate_parts(rows: list[Row], issues: list[ValidationIssue]) -> None:
    for row_number, row in enumerate(rows, start=2):
        cost = _parse_decimal_or_none(row.get("unit_cost_eur", ""))
        lead = _parse_int_or_none(row.get("standard_lead_time_days", ""))
        if cost is not None and cost < 0:
            issues.append(
                _domain_issue(
                    "parts",
                    row_number,
                    row,
                    "unit_cost_eur",
                    "NEGATIVE_MONETARY_VALUE",
                    "Part unit cost cannot be negative.",
                )
            )
        if lead is not None and lead < 0:
            issues.append(
                _domain_issue(
                    "parts",
                    row_number,
                    row,
                    "standard_lead_time_days",
                    "INVALID_NUMERIC_VALUE",
                    "Part lead time cannot be negative.",
                )
            )


def _validate_order_parts(rows: list[Row], issues: list[ValidationIssue]) -> None:
    for row_number, row in enumerate(rows, start=2):
        quantity = _parse_int_or_none(row.get("quantity", ""))
        line_number = _parse_int_or_none(row.get("line_number", ""))
        cost = _parse_decimal_or_none(row.get("unit_cost_eur", ""))
        requested = _parse_datetime_or_none(row.get("requested_at", ""))
        required = _parse_datetime_or_none(row.get("required_at", ""))
        delivered = _parse_datetime_or_none(row.get("delivered_at", ""))

        for field, value in (("quantity", quantity), ("line_number", line_number)):
            if value is not None and value <= 0:
                issues.append(
                    _domain_issue(
                        "service_order_parts",
                        row_number,
                        row,
                        field,
                        "INVALID_NUMERIC_VALUE",
                        f"{field} must be positive.",
                    )
                )
        if cost is not None and cost < 0:
            issues.append(
                _domain_issue(
                    "service_order_parts",
                    row_number,
                    row,
                    "unit_cost_eur",
                    "NEGATIVE_MONETARY_VALUE",
                    "Service-order part cost cannot be negative.",
                )
            )
        for earlier, later, field, message in (
            (requested, required, "required_at", "Required timestamp precedes request."),
            (requested, delivered, "delivered_at", "Delivery precedes request."),
        ):
            if earlier is not None and later is not None and later < earlier:
                issues.append(
                    _domain_issue(
                        "service_order_parts",
                        row_number,
                        row,
                        field,
                        "INVALID_TIMESTAMP_ORDER",
                        message,
                    )
                )


def _validate_costs(rows: list[Row], issues: list[ValidationIssue]) -> None:
    for row_number, row in enumerate(rows, start=2):
        amount = _parse_decimal_or_none(row.get("cost_amount_eur", ""))
        if amount is not None and amount < 0:
            issues.append(
                _domain_issue(
                    "service_costs",
                    row_number,
                    row,
                    "cost_amount_eur",
                    "NEGATIVE_MONETARY_VALUE",
                    "Service cost cannot be negative.",
                )
            )


def _validate_alerts(
    rows: list[Row],
    cases: dict[str, Row],
    assets: dict[str, Row],
    issues: list[ValidationIssue],
) -> None:
    for row_number, row in enumerate(rows, start=2):
        raised = _parse_datetime_or_none(row.get("raised_at", ""))
        acknowledged = _parse_datetime_or_none(row.get("acknowledged_at", ""))
        cleared = _parse_datetime_or_none(row.get("cleared_at", ""))
        for later, field, message in (
            (acknowledged, "acknowledged_at", "Acknowledgement precedes alert creation."),
            (cleared, "cleared_at", "Clearance precedes alert creation."),
        ):
            if raised is not None and later is not None and later < raised:
                issues.append(
                    _domain_issue(
                        "equipment_alerts",
                        row_number,
                        row,
                        field,
                        "INVALID_TIMESTAMP_ORDER",
                        message,
                    )
                )

        case_id = row.get("related_case_id", "")
        if case_id:
            case = cases.get(case_id)
            if case is not None and case.get("asset_id") != row.get("asset_id"):
                issues.append(
                    _domain_issue(
                        "equipment_alerts",
                        row_number,
                        row,
                        "related_case_id",
                        "INCONSISTENT_RELATIONSHIP",
                        "Alert and linked case refer to different assets.",
                    )
                )
        if row.get("asset_id", "") not in assets:
            continue


def _validate_notes(rows: list[Row], orders: dict[str, Row], issues: list[ValidationIssue]) -> None:
    for row_number, row in enumerate(rows, start=2):
        if not row.get("note_text", "").strip():
            issues.append(
                _domain_issue(
                    "technician_notes",
                    row_number,
                    row,
                    "note_text",
                    "MALFORMED_TEXT",
                    "Technician note text is empty or whitespace only.",
                )
            )
        order = orders.get(row.get("service_order_id", ""))
        created = _parse_datetime_or_none(row.get("created_at", ""))
        order_created = _parse_datetime_or_none(order.get("created_at", "")) if order else None
        if created is not None and order_created is not None and created < order_created:
            issues.append(
                _domain_issue(
                    "technician_notes",
                    row_number,
                    row,
                    "created_at",
                    "INVALID_TIMESTAMP_ORDER",
                    "Technician note predates the service order.",
                )
            )


def _value_matches_type(value: str, declared_type: str) -> bool:
    try:
        if declared_type == "string":
            return True
        if declared_type == "integer":
            int(value)
            return True
        if declared_type.startswith("decimal_"):
            Decimal(value)
            return True
        if declared_type == "date":
            date.fromisoformat(value)
            return True
        if declared_type == "timestamp_utc":
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.tzinfo is not None
    except (ValueError, InvalidOperation):
        return False
    return False


def _business_key(row: Row, fields: list[str]) -> str:
    return "|".join(row.get(field, "") for field in fields)


def _index(rows: list[Row], field: str) -> dict[str, Row]:
    return {row.get(field, ""): row for row in rows if row.get(field, "")}


def _issue(
    dataset: str,
    row_number: int,
    field: str,
    code: str,
    message: str,
    business_key: str,
) -> ValidationIssue:
    return ValidationIssue(dataset, row_number, field, code, message, business_key)


def _domain_issue(
    dataset: str,
    row_number: int,
    row: Row,
    field: str,
    code: str,
    message: str,
) -> ValidationIssue:
    key_fields = {
        "customers": ["customer_id"],
        "sites": ["site_id"],
        "assets": ["asset_id"],
        "service_contracts": ["contract_id"],
        "customer_cases": ["case_id"],
        "case_status_history": ["case_status_event_id"],
        "technicians": ["technician_id"],
        "service_orders": ["service_order_id"],
        "parts": ["part_id"],
        "service_order_parts": ["service_order_id", "part_id", "line_number"],
        "service_costs": ["service_cost_id"],
        "equipment_alerts": ["alert_id"],
        "technician_notes": ["note_id"],
    }
    return _issue(
        dataset,
        row_number,
        field,
        code,
        message,
        _business_key(row, key_fields[dataset]),
    )


def _parse_datetime_or_none(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_date_or_none(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_int_or_none(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _parse_decimal_or_none(value: str) -> Decimal | None:
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _issue_sort_key(issue: ValidationIssue) -> tuple[str, int, str, str]:
    return (issue.dataset, issue.row_number, issue.field, issue.code)
