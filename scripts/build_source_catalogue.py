from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "config" / "source_schema.json"
DICTIONARY_PATH = ROOT / "docs" / "data_dictionary.md"
ERD_PATH = ROOT / "docs" / "entity_relationship_diagram.md"
SUMMARY_PATH = ROOT / "docs" / "data_model_summary.md"

CASE_STATUSES = [
    "OPEN",
    "ASSIGNED",
    "IN_PROGRESS",
    "WAITING_PARTS",
    "RESOLVED",
    "CLOSED",
    "CANCELLED",
]

REGIONS = ["NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"]

FAULT_CATEGORIES = [
    "BEARING",
    "VIBRATION",
    "OVERHEATING",
    "LUBRICATION",
    "SEAL",
    "ELECTRICAL",
    "CONTROL_SYSTEM",
    "PRESSURE",
    "FLOW",
    "INSPECTION",
    "OTHER",
]


def field(
    name: str,
    data_type: str,
    nullable: bool,
    description: str,
    *,
    allowed_values: list[str] | None = None,
    references: str | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "name": name,
        "type": data_type,
        "nullable": nullable,
        "description": description,
    }
    if allowed_values is not None:
        item["allowed_values"] = allowed_values
    if references is not None:
        item["references"] = references
    return item


def audit_fields() -> list[dict[str, Any]]:
    return [
        field(
            "created_at",
            "timestamp_utc",
            False,
            "Timestamp when the source record was created.",
        ),
        field(
            "updated_at",
            "timestamp_utc",
            False,
            "Timestamp of the latest source update.",
        ),
    ]


DATASETS: dict[str, dict[str, Any]] = {
    "customers": {
        "source_area": "ERP",
        "file_name": "customers.csv",
        "raw_table": "RAW.ERP_CUSTOMERS",
        "staging_model": "stg_erp_customers",
        "core_target": "CORE.DIM_CUSTOMER",
        "business_key": ["customer_id"],
        "fields": [
            field(
                "customer_id",
                "string",
                False,
                "Stable customer business identifier.",
            ),
            field(
                "customer_name",
                "string",
                False,
                "Fictional organisation name.",
            ),
            field(
                "industry",
                "string",
                False,
                "Customer industry grouping.",
                allowed_values=[
                    "ENERGY",
                    "CHEMICALS",
                    "MANUFACTURING",
                    "MINING",
                    "UTILITIES",
                ],
            ),
            field(
                "customer_region",
                "string",
                False,
                "Commercial region assigned to the customer.",
                allowed_values=REGIONS,
            ),
            field(
                "customer_status",
                "string",
                False,
                "Current customer status.",
                allowed_values=["ACTIVE", "INACTIVE"],
            ),
            *audit_fields(),
        ],
    },
    "sites": {
        "source_area": "ERP",
        "file_name": "sites.csv",
        "raw_table": "RAW.ERP_SITES",
        "staging_model": "stg_erp_sites",
        "core_target": "CORE.DIM_SITE",
        "business_key": ["site_id"],
        "fields": [
            field("site_id", "string", False, "Stable site business identifier."),
            field(
                "customer_id",
                "string",
                False,
                "Customer that owns or operates the site.",
                references="customers.customer_id",
            ),
            field("site_name", "string", False, "Fictional site name."),
            field(
                "country_code",
                "string",
                False,
                "Uppercase two-letter country code.",
            ),
            field(
                "region",
                "string",
                False,
                "Operational service region.",
                allowed_values=REGIONS,
            ),
            field(
                "timezone",
                "string",
                False,
                "IANA-style time-zone name for the site.",
            ),
            field(
                "site_status",
                "string",
                False,
                "Current site status.",
                allowed_values=["ACTIVE", "INACTIVE"],
            ),
            *audit_fields(),
        ],
    },
    "assets": {
        "source_area": "ERP",
        "file_name": "assets.csv",
        "raw_table": "RAW.ERP_ASSETS",
        "staging_model": "stg_erp_assets",
        "core_target": "CORE.DIM_ASSET",
        "business_key": ["asset_id"],
        "fields": [
            field("asset_id", "string", False, "Stable asset business identifier."),
            field(
                "site_id",
                "string",
                False,
                "Site where the asset is installed.",
                references="sites.site_id",
            ),
            field("asset_name", "string", False, "Readable asset label."),
            field(
                "asset_type",
                "string",
                False,
                "Controlled equipment type.",
                allowed_values=[
                    "GAS_TURBINE",
                    "STEAM_TURBINE",
                    "COMPRESSOR",
                    "INDUSTRIAL_PUMP",
                ],
            ),
            field(
                "manufacturer",
                "string",
                False,
                "Fictional equipment manufacturer.",
            ),
            field("model", "string", False, "Equipment model designation."),
            field(
                "serial_number",
                "string",
                False,
                "Unique source serial number.",
            ),
            field(
                "installation_date",
                "date",
                False,
                "Date the asset entered service.",
            ),
            field(
                "criticality",
                "string",
                False,
                "Operational importance of the asset.",
                allowed_values=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            ),
            field(
                "asset_status",
                "string",
                False,
                "Current asset lifecycle status.",
                allowed_values=["ACTIVE", "OUT_OF_SERVICE", "RETIRED"],
            ),
            *audit_fields(),
        ],
    },
    "service_contracts": {
        "source_area": "CRM",
        "file_name": "service_contracts.csv",
        "raw_table": "RAW.CRM_SERVICE_CONTRACTS",
        "staging_model": "stg_crm_service_contracts",
        "core_target": "CORE.DIM_SERVICE_CONTRACT",
        "business_key": ["contract_id"],
        "fields": [
            field(
                "contract_id",
                "string",
                False,
                "Stable service-contract business identifier.",
            ),
            field(
                "customer_id",
                "string",
                False,
                "Customer covered by the contract.",
                references="customers.customer_id",
            ),
            field(
                "site_id",
                "string",
                False,
                "Site covered by the contract.",
                references="sites.site_id",
            ),
            field(
                "contract_type",
                "string",
                False,
                "Service coverage level.",
                allowed_values=["BASIC", "STANDARD", "PREMIUM"],
            ),
            field("start_date", "date", False, "Contract start date."),
            field("end_date", "date", False, "Contract end date."),
            field(
                "response_sla_hours",
                "integer",
                False,
                "Allowed elapsed hours to first response.",
            ),
            field(
                "resolution_sla_hours",
                "integer",
                False,
                "Allowed elapsed hours to case resolution.",
            ),
            field(
                "contract_status",
                "string",
                False,
                "Current contract status.",
                allowed_values=["DRAFT", "ACTIVE", "EXPIRED", "CANCELLED"],
            ),
            *audit_fields(),
        ],
    },
    "customer_cases": {
        "source_area": "CRM",
        "file_name": "customer_cases.csv",
        "raw_table": "RAW.CRM_CUSTOMER_CASES",
        "staging_model": "stg_crm_customer_cases",
        "core_target": "CORE.FACT_SERVICE_CASE",
        "business_key": ["case_id"],
        "fields": [
            field("case_id", "string", False, "Stable case business identifier."),
            field(
                "customer_id",
                "string",
                False,
                "Customer that raised the case.",
                references="customers.customer_id",
            ),
            field(
                "site_id",
                "string",
                False,
                "Site associated with the case.",
                references="sites.site_id",
            ),
            field(
                "contract_id",
                "string",
                True,
                "Applicable service contract when one exists.",
                references="service_contracts.contract_id",
            ),
            field(
                "asset_id",
                "string",
                True,
                "Asset associated with the case when relevant.",
                references="assets.asset_id",
            ),
            field(
                "case_type",
                "string",
                False,
                "Reason the case was opened.",
                allowed_values=[
                    "TECHNICAL_FAULT",
                    "INSPECTION_REQUEST",
                    "MAINTENANCE_REQUEST",
                    "GENERAL_ENQUIRY",
                ],
            ),
            field(
                "priority",
                "string",
                False,
                "Operational priority assigned to the case.",
                allowed_values=["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            ),
            field(
                "fault_category",
                "string",
                True,
                "Controlled fault category when the case concerns equipment.",
                allowed_values=FAULT_CATEGORIES,
            ),
            field(
                "case_status",
                "string",
                False,
                "Current case status.",
                allowed_values=CASE_STATUSES,
            ),
            field("created_at", "timestamp_utc", False, "Case creation timestamp."),
            field(
                "response_due_at",
                "timestamp_utc",
                False,
                "Deadline for the first response.",
            ),
            field(
                "resolution_due_at",
                "timestamp_utc",
                False,
                "Deadline for case resolution.",
            ),
            field(
                "first_response_at",
                "timestamp_utc",
                True,
                "Timestamp of the first recorded response.",
            ),
            field(
                "resolved_at",
                "timestamp_utc",
                True,
                "Timestamp of the first valid resolution.",
            ),
            field(
                "closed_at",
                "timestamp_utc",
                True,
                "Timestamp when the case was closed.",
            ),
            field(
                "updated_at",
                "timestamp_utc",
                False,
                "Timestamp of the latest source update.",
            ),
        ],
    },
    "case_status_history": {
        "source_area": "CRM",
        "file_name": "case_status_history.csv",
        "raw_table": "RAW.CRM_CASE_STATUS_HISTORY",
        "staging_model": "stg_crm_case_status_history",
        "core_target": "CORE.FACT_CASE_STATUS_EVENT",
        "business_key": ["case_status_event_id"],
        "fields": [
            field(
                "case_status_event_id",
                "string",
                False,
                "Stable status-event business identifier.",
            ),
            field(
                "case_id",
                "string",
                False,
                "Case affected by the status change.",
                references="customer_cases.case_id",
            ),
            field(
                "previous_status",
                "string",
                True,
                "Status before the change; null for the first event.",
                allowed_values=CASE_STATUSES,
            ),
            field(
                "new_status",
                "string",
                False,
                "Status after the change.",
                allowed_values=CASE_STATUSES,
            ),
            field(
                "changed_at",
                "timestamp_utc",
                False,
                "Timestamp when the status changed.",
            ),
            field(
                "change_reason",
                "string",
                False,
                "Short explanation recorded with the transition.",
            ),
        ],
    },
    "technicians": {
        "source_area": "ERP",
        "file_name": "technicians.csv",
        "raw_table": "RAW.ERP_TECHNICIANS",
        "staging_model": "stg_erp_technicians",
        "core_target": "CORE.DIM_TECHNICIAN",
        "business_key": ["technician_id"],
        "fields": [
            field(
                "technician_id",
                "string",
                False,
                "Stable technician business identifier.",
            ),
            field(
                "technician_name",
                "string",
                False,
                "Fictional technician name.",
            ),
            field(
                "home_region",
                "string",
                False,
                "Technician's normal service region.",
                allowed_values=REGIONS,
            ),
            field(
                "specialisation",
                "string",
                False,
                "Primary technical specialisation.",
                allowed_values=[
                    "ROTATING_EQUIPMENT",
                    "ELECTRICAL",
                    "CONTROLS",
                    "INSTRUMENTATION",
                    "GENERAL",
                ],
            ),
            field(
                "skill_level",
                "string",
                False,
                "Experience band used for generated assignments.",
                allowed_values=["JUNIOR", "INTERMEDIATE", "SENIOR", "EXPERT"],
            ),
            field(
                "technician_status",
                "string",
                False,
                "Current technician status.",
                allowed_values=["ACTIVE", "INACTIVE"],
            ),
            *audit_fields(),
        ],
    },
    "service_orders": {
        "source_area": "ERP",
        "file_name": "service_orders.csv",
        "raw_table": "RAW.ERP_SERVICE_ORDERS",
        "staging_model": "stg_erp_service_orders",
        "core_target": "CORE.FACT_SERVICE_ORDER",
        "business_key": ["service_order_id"],
        "fields": [
            field(
                "service_order_id",
                "string",
                False,
                "Stable service-order business identifier.",
            ),
            field(
                "case_id",
                "string",
                True,
                "Related customer case when the order is reactive.",
                references="customer_cases.case_id",
            ),
            field(
                "asset_id",
                "string",
                False,
                "Asset receiving the service work.",
                references="assets.asset_id",
            ),
            field(
                "lead_technician_id",
                "string",
                False,
                "Lead technician assigned to the order.",
                references="technicians.technician_id",
            ),
            field(
                "order_type",
                "string",
                False,
                "Type of service activity.",
                allowed_values=[
                    "INSPECTION",
                    "CORRECTIVE_REPAIR",
                    "PREVENTIVE_MAINTENANCE",
                    "EMERGENCY_REPAIR",
                ],
            ),
            field(
                "order_status",
                "string",
                False,
                "Current service-order status.",
                allowed_values=[
                    "PLANNED",
                    "DISPATCHED",
                    "IN_PROGRESS",
                    "COMPLETED",
                    "CANCELLED",
                ],
            ),
            field(
                "created_at",
                "timestamp_utc",
                False,
                "Service-order creation timestamp.",
            ),
            field(
                "scheduled_start_at",
                "timestamp_utc",
                False,
                "Planned start timestamp.",
            ),
            field(
                "actual_start_at",
                "timestamp_utc",
                True,
                "Actual start timestamp when work has begun.",
            ),
            field(
                "completed_at",
                "timestamp_utc",
                True,
                "Completion timestamp for completed work.",
            ),
            field(
                "downtime_start_at",
                "timestamp_utc",
                True,
                "Start of the associated equipment downtime interval.",
            ),
            field(
                "downtime_end_at",
                "timestamp_utc",
                True,
                "End of the associated equipment downtime interval.",
            ),
            field(
                "resolution_code",
                "string",
                True,
                "Outcome recorded when the order is completed.",
                allowed_values=[
                    "FIXED",
                    "ADJUSTED",
                    "REPLACED_COMPONENT",
                    "NO_FAULT_FOUND",
                    "FOLLOW_UP_REQUIRED",
                    "NOT_COMPLETED",
                ],
            ),
            field(
                "created_by_source",
                "string",
                False,
                "Source process that created the service order.",
                allowed_values=["CRM_CASE", "PLANNED_MAINTENANCE", "MONITORING_ALERT"],
            ),
        ],
    },
    "parts": {
        "source_area": "ERP",
        "file_name": "parts.csv",
        "raw_table": "RAW.ERP_PARTS",
        "staging_model": "stg_erp_parts",
        "core_target": "CORE.DIM_PART",
        "business_key": ["part_id"],
        "fields": [
            field("part_id", "string", False, "Stable part business identifier."),
            field("part_name", "string", False, "Fictional spare-part name."),
            field(
                "part_category",
                "string",
                False,
                "Controlled spare-part category.",
                allowed_values=[
                    "BEARING",
                    "SEAL",
                    "LUBRICATION",
                    "ELECTRICAL",
                    "CONTROL",
                    "VALVE",
                    "FILTER",
                    "FASTENER",
                    "OTHER",
                ],
            ),
            field(
                "unit_cost_eur",
                "decimal_18_2",
                False,
                "Standard unit cost in EUR.",
            ),
            field(
                "standard_lead_time_days",
                "integer",
                False,
                "Expected supplier lead time in elapsed days.",
            ),
            field(
                "part_status",
                "string",
                False,
                "Current part status.",
                allowed_values=["ACTIVE", "OBSOLETE"],
            ),
            *audit_fields(),
        ],
    },
    "service_order_parts": {
        "source_area": "ERP",
        "file_name": "service_order_parts.csv",
        "raw_table": "RAW.ERP_SERVICE_ORDER_PARTS",
        "staging_model": "stg_erp_service_order_parts",
        "core_target": "CORE.FACT_SERVICE_ORDER_PART",
        "business_key": ["service_order_id", "part_id", "line_number"],
        "fields": [
            field(
                "service_order_id",
                "string",
                False,
                "Service order that requested or used the part.",
                references="service_orders.service_order_id",
            ),
            field(
                "part_id",
                "string",
                False,
                "Requested or consumed part.",
                references="parts.part_id",
            ),
            field(
                "line_number",
                "integer",
                False,
                "Line number unique within the order and part combination.",
            ),
            field("quantity", "integer", False, "Positive quantity requested."),
            field(
                "requested_at",
                "timestamp_utc",
                False,
                "Timestamp when the part was requested.",
            ),
            field(
                "required_at",
                "timestamp_utc",
                False,
                "Timestamp by which the part was required.",
            ),
            field(
                "delivered_at",
                "timestamp_utc",
                True,
                "Actual delivery timestamp; null while outstanding.",
            ),
            field(
                "unit_cost_eur",
                "decimal_18_2",
                False,
                "Unit cost recorded on the service-order line.",
            ),
        ],
    },
    "service_costs": {
        "source_area": "ERP",
        "file_name": "service_costs.csv",
        "raw_table": "RAW.ERP_SERVICE_COSTS",
        "staging_model": "stg_erp_service_costs",
        "core_target": "CORE.FACT_SERVICE_COST",
        "business_key": ["service_cost_id"],
        "fields": [
            field(
                "service_cost_id",
                "string",
                False,
                "Stable service-cost transaction identifier.",
            ),
            field(
                "service_order_id",
                "string",
                False,
                "Service order receiving the cost.",
                references="service_orders.service_order_id",
            ),
            field(
                "cost_type",
                "string",
                False,
                "Type of service expenditure.",
                allowed_values=[
                    "LABOUR",
                    "TRAVEL",
                    "PART",
                    "EXTERNAL_SERVICE",
                ],
            ),
            field(
                "cost_amount_eur",
                "decimal_18_2",
                False,
                "Transaction amount in EUR.",
            ),
            field(
                "cost_recorded_at",
                "timestamp_utc",
                False,
                "Timestamp when the cost was recorded.",
            ),
        ],
    },
    "equipment_alerts": {
        "source_area": "Monitoring",
        "file_name": "equipment_alerts.csv",
        "raw_table": "RAW.MONITORING_EQUIPMENT_ALERTS",
        "staging_model": "stg_monitoring_equipment_alerts",
        "core_target": "CORE.FACT_EQUIPMENT_ALERT",
        "business_key": ["alert_id"],
        "fields": [
            field("alert_id", "string", False, "Stable alert business identifier."),
            field(
                "asset_id",
                "string",
                False,
                "Asset that generated the alert.",
                references="assets.asset_id",
            ),
            field(
                "related_case_id",
                "string",
                True,
                "Customer case explicitly linked to the alert.",
                references="customer_cases.case_id",
            ),
            field(
                "alert_type",
                "string",
                False,
                "Condition represented by the alert.",
                allowed_values=[
                    "VIBRATION",
                    "TEMPERATURE",
                    "PRESSURE",
                    "FLOW",
                    "LUBRICATION",
                    "ELECTRICAL",
                    "CONTROL_SYSTEM",
                ],
            ),
            field(
                "severity",
                "string",
                False,
                "Operational severity of the alert.",
                allowed_values=["INFO", "WARNING", "CRITICAL"],
            ),
            field(
                "alert_status",
                "string",
                False,
                "Current alert state.",
                allowed_values=["OPEN", "ACKNOWLEDGED", "CLEARED"],
            ),
            field(
                "raised_at",
                "timestamp_utc",
                False,
                "Timestamp when the alert was raised.",
            ),
            field(
                "acknowledged_at",
                "timestamp_utc",
                True,
                "Timestamp of manual or automatic acknowledgement.",
            ),
            field(
                "cleared_at",
                "timestamp_utc",
                True,
                "Timestamp when the alert was cleared.",
            ),
            field(
                "measured_value",
                "decimal_18_6",
                True,
                "Measured value when the alert is numeric.",
            ),
            field(
                "threshold_value",
                "decimal_18_6",
                True,
                "Configured threshold when the alert is numeric.",
            ),
            field(
                "measurement_unit",
                "string",
                True,
                "Unit used for measured and threshold values.",
            ),
        ],
    },
    "technician_notes": {
        "source_area": "Field service",
        "file_name": "technician_notes.csv",
        "raw_table": "RAW.FIELD_SERVICE_TECHNICIAN_NOTES",
        "staging_model": "stg_field_service_technician_notes",
        "core_target": "CORE.FACT_TECHNICIAN_NOTE",
        "business_key": ["note_id"],
        "fields": [
            field("note_id", "string", False, "Stable note business identifier."),
            field(
                "service_order_id",
                "string",
                False,
                "Service order documented by the note.",
                references="service_orders.service_order_id",
            ),
            field(
                "technician_id",
                "string",
                False,
                "Technician who authored the note.",
                references="technicians.technician_id",
            ),
            field(
                "note_type",
                "string",
                False,
                "Stage of field work represented by the note.",
                allowed_values=["INSPECTION", "DIAGNOSIS", "REPAIR", "COMPLETION"],
            ),
            field(
                "note_text",
                "string",
                False,
                "Original free-text field-service observation.",
            ),
            field(
                "created_at",
                "timestamp_utc",
                False,
                "Timestamp when the note was created.",
            ),
        ],
    },
}

RELATIONSHIPS = [
    {
        "parent": "customers",
        "child": "sites",
        "child_field": "customer_id",
        "connector": "||--o{",
        "label": "owns",
    },
    {
        "parent": "customers",
        "child": "service_contracts",
        "child_field": "customer_id",
        "connector": "||--o{",
        "label": "holds",
    },
    {
        "parent": "sites",
        "child": "service_contracts",
        "child_field": "site_id",
        "connector": "||--o{",
        "label": "covered by",
    },
    {
        "parent": "sites",
        "child": "assets",
        "child_field": "site_id",
        "connector": "||--o{",
        "label": "contains",
    },
    {
        "parent": "customers",
        "child": "customer_cases",
        "child_field": "customer_id",
        "connector": "||--o{",
        "label": "raises",
    },
    {
        "parent": "sites",
        "child": "customer_cases",
        "child_field": "site_id",
        "connector": "||--o{",
        "label": "reports",
    },
    {
        "parent": "service_contracts",
        "child": "customer_cases",
        "child_field": "contract_id",
        "connector": "o|--o{",
        "label": "governs",
    },
    {
        "parent": "assets",
        "child": "customer_cases",
        "child_field": "asset_id",
        "connector": "o|--o{",
        "label": "concerns",
    },
    {
        "parent": "customer_cases",
        "child": "case_status_history",
        "child_field": "case_id",
        "connector": "||--|{",
        "label": "has history",
    },
    {
        "parent": "customer_cases",
        "child": "service_orders",
        "child_field": "case_id",
        "connector": "o|--o{",
        "label": "creates",
    },
    {
        "parent": "assets",
        "child": "service_orders",
        "child_field": "asset_id",
        "connector": "||--o{",
        "label": "receives",
    },
    {
        "parent": "technicians",
        "child": "service_orders",
        "child_field": "lead_technician_id",
        "connector": "||--o{",
        "label": "leads",
    },
    {
        "parent": "service_orders",
        "child": "service_order_parts",
        "child_field": "service_order_id",
        "connector": "||--o{",
        "label": "uses",
    },
    {
        "parent": "parts",
        "child": "service_order_parts",
        "child_field": "part_id",
        "connector": "||--o{",
        "label": "appears on",
    },
    {
        "parent": "service_orders",
        "child": "service_costs",
        "child_field": "service_order_id",
        "connector": "||--o{",
        "label": "incurs",
    },
    {
        "parent": "assets",
        "child": "equipment_alerts",
        "child_field": "asset_id",
        "connector": "||--o{",
        "label": "generates",
    },
    {
        "parent": "customer_cases",
        "child": "equipment_alerts",
        "child_field": "related_case_id",
        "connector": "o|--o{",
        "label": "linked to",
    },
    {
        "parent": "service_orders",
        "child": "technician_notes",
        "child_field": "service_order_id",
        "connector": "||--o{",
        "label": "documents",
    },
    {
        "parent": "technicians",
        "child": "technician_notes",
        "child_field": "technician_id",
        "connector": "||--o{",
        "label": "writes",
    },
]


def validate_catalogue() -> None:
    expected_datasets = {
        "customers",
        "sites",
        "assets",
        "service_contracts",
        "customer_cases",
        "case_status_history",
        "service_orders",
        "technicians",
        "parts",
        "service_order_parts",
        "service_costs",
        "equipment_alerts",
        "technician_notes",
    }
    if set(DATASETS) != expected_datasets:
        missing = sorted(expected_datasets - set(DATASETS))
        unexpected = sorted(set(DATASETS) - expected_datasets)
        raise ValueError(f"Dataset mismatch. Missing={missing}, unexpected={unexpected}")

    raw_tables: set[str] = set()
    staging_models: set[str] = set()
    core_targets: set[str] = set()

    for dataset_name, dataset in DATASETS.items():
        fields = dataset["fields"]
        field_names = [item["name"] for item in fields]

        if len(field_names) != len(set(field_names)):
            raise ValueError(f"Duplicate field in dataset {dataset_name}")

        business_key = dataset["business_key"]
        for key_field in business_key:
            if key_field not in field_names:
                raise ValueError(f"Business key {dataset_name}.{key_field} is not defined")
            field_spec = next(item for item in fields if item["name"] == key_field)
            if field_spec["nullable"]:
                raise ValueError(f"Business key {dataset_name}.{key_field} cannot be nullable")

        for item in fields:
            if not item["description"].strip():
                raise ValueError(f"Missing description for {dataset_name}.{item['name']}")

            reference = item.get("references")
            if reference is None:
                continue

            parent_dataset, parent_field = reference.split(".", maxsplit=1)
            if parent_dataset not in DATASETS:
                raise ValueError(f"Unknown referenced dataset in {dataset_name}.{item['name']}")
            parent_fields = {
                parent_item["name"] for parent_item in DATASETS[parent_dataset]["fields"]
            }
            if parent_field not in parent_fields:
                raise ValueError(f"Unknown referenced field in {dataset_name}.{item['name']}")

        for key, seen in [
            ("raw_table", raw_tables),
            ("staging_model", staging_models),
            ("core_target", core_targets),
        ]:
            value = dataset[key]
            if value in seen:
                raise ValueError(f"Duplicate {key}: {value}")
            seen.add(value)

    for relationship in RELATIONSHIPS:
        child_dataset = relationship["child"]
        child_field = relationship["child_field"]
        parent_dataset = relationship["parent"]

        child_fields = {item["name"]: item for item in DATASETS[child_dataset]["fields"]}
        if child_field not in child_fields:
            raise ValueError(f"Relationship field missing: {child_dataset}.{child_field}")

        expected_reference_prefix = f"{parent_dataset}."
        reference = child_fields[child_field].get("references", "")
        if not reference.startswith(expected_reference_prefix):
            raise ValueError(
                f"Relationship does not match field reference: {child_dataset}.{child_field}"
            )


def write_schema_json() -> None:
    payload = {
        "schema_version": "1.0.0",
        "datasets": DATASETS,
        "relationships": RELATIONSHIPS,
    }
    SCHEMA_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def escape_markdown(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ")


def field_key_label(
    field_spec: dict[str, Any],
    business_key: list[str],
) -> str:
    labels: list[str] = []
    if field_spec["name"] in business_key:
        labels.append("PK")
    reference = field_spec.get("references")
    if reference is not None:
        labels.append(f"FK to `{reference}`")
    return ", ".join(labels) if labels else "—"


def write_data_dictionary() -> None:
    lines = [
        "# Source data dictionary",
        "",
        "This dictionary is generated from `config/source_schema.json`.",
        "The JSON catalogue is the machine-readable source of truth for synthetic data generation.",
        "",
        "## Type conventions",
        "",
        "| Type | Meaning |",
        "|---|---|",
        "| `string` | UTF-8 text |",
        "| `integer` | Whole number |",
        "| `date` | Calendar date in ISO `YYYY-MM-DD` form |",
        "| `timestamp_utc` | UTC timestamp in ISO 8601 form |",
        "| `decimal_18_2` | Fixed-precision monetary value |",
        "| `decimal_18_6` | Fixed-precision measurement value |",
        "",
    ]

    for dataset_name, dataset in DATASETS.items():
        lines.extend(
            [
                f"## {dataset_name}",
                "",
                f"- Source area: {dataset['source_area']}",
                f"- Source file: `{dataset['file_name']}`",
                f"- Raw table: `{dataset['raw_table']}`",
                f"- Staging model: `{dataset['staging_model']}`",
                f"- Core target: `{dataset['core_target']}`",
                "- Business key: " + ", ".join(f"`{item}`" for item in dataset["business_key"]),
                "",
                "| Field | Type | Nullable | Key or reference | Allowed values | Description |",
                "|---|---|---:|---|---|---|",
            ]
        )

        for field_spec in dataset["fields"]:
            allowed = field_spec.get("allowed_values")
            allowed_text = ", ".join(f"`{value}`" for value in allowed) if allowed else "—"
            nullable = "Yes" if field_spec["nullable"] else "No"
            key_label = field_key_label(
                field_spec,
                dataset["business_key"],
            )
            lines.append(
                "| "
                f"`{field_spec['name']}` | "
                f"`{field_spec['type']}` | "
                f"{nullable} | "
                f"{key_label} | "
                f"{allowed_text} | "
                f"{escape_markdown(field_spec['description'])} |"
            )

        lines.append("")

    DICTIONARY_PATH.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def mermaid_type(data_type: str) -> str:
    mapping = {
        "string": "string",
        "integer": "int",
        "date": "date",
        "timestamp_utc": "datetime",
        "decimal_18_2": "decimal",
        "decimal_18_6": "decimal",
    }
    return mapping[data_type]


def write_erd() -> None:
    fence = "`" * 3
    lines = [
        "# Entity relationship diagram",
        "",
        "This diagram shows the source-level business entities and their keys.",
        "Optional links remain nullable in the source catalogue.",
        "",
        f"{fence}mermaid",
        "erDiagram",
    ]

    for dataset_name, dataset in DATASETS.items():
        lines.append(f"    {dataset_name.upper()} {{")
        for field_spec in dataset["fields"]:
            key_markers: list[str] = []
            if field_spec["name"] in dataset["business_key"]:
                key_markers.append("PK")
            if "references" in field_spec:
                key_markers.append("FK")
            key_text = f" {', '.join(key_markers)}" if key_markers else ""
            lines.append(
                f"        {mermaid_type(field_spec['type'])} {field_spec['name']}{key_text}"
            )
        lines.append("    }")

    for relationship in RELATIONSHIPS:
        lines.append(
            "    "
            f"{relationship['parent'].upper()} "
            f"{relationship['connector']} "
            f"{relationship['child'].upper()} "
            f": {relationship['label']}"
        )

    lines.append(fence)
    lines.append("")

    ERD_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_phase_summary() -> None:
    lines = [
        "# Data model review",
        "",
        "The data model fixes the business meaning of the project before source generation.",
        "The following artefacts now define the scope:",
        "",
        "- `docs/business_context.md` — users, decisions, assumptions, and limits;",
        "- `docs/conceptual_data_model.md` — entities and lifecycle rules;",
        "- `docs/kpi_catalogue.md` — formulas, eligibility rules, and edge cases;",
        "- `docs/source_to_target_mapping.md` — warehouse lineage and handling rules;",
        "- `config/source_schema.json` — machine-readable source definitions;",
        "- `docs/data_dictionary.md` — generated field-level reference;",
        "- `docs/entity_relationship_diagram.md` — source-level ER diagram.",
        "",
        "## Phase gate",
        "",
        "- Thirteen source datasets are defined.",
        "- Every dataset has a business key.",
        "- Every foreign-key reference resolves to an existing field.",
        "- KPI formulas identify their source fields and edge-case treatment.",
        "- Source, raw, staging, core, and analytical layers are mapped.",
        "- The asset dimension is marked for historical tracking.",
        "- Deliberate simplifications and out-of-scope areas are documented.",
        "",
        "The source generator can now work against a fixed contract instead of",
        "inventing fields while the generator is being written.",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    validate_catalogue()
    write_schema_json()
    write_data_dictionary()
    write_erd()
    write_phase_summary()

    print(
        "Source catalogue generated: "
        f"{len(DATASETS)} datasets, "
        f"{sum(len(item['fields']) for item in DATASETS.values())} fields, "
        f"{len(RELATIONSHIPS)} relationships"
    )


if __name__ == "__main__":
    main()
