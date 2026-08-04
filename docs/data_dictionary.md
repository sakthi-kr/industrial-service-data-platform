# Source data dictionary

This dictionary is generated from `config/source_schema.json`.
The JSON catalogue is the machine-readable source of truth for synthetic data generation.

## Type conventions

| Type | Meaning |
|---|---|
| `string` | UTF-8 text |
| `integer` | Whole number |
| `date` | Calendar date in ISO `YYYY-MM-DD` form |
| `timestamp_utc` | UTC timestamp in ISO 8601 form |
| `decimal_18_2` | Fixed-precision monetary value |
| `decimal_18_6` | Fixed-precision measurement value |

## customers

- Source area: ERP
- Source file: `customers.csv`
- Raw table: `RAW.ERP_CUSTOMERS`
- Staging model: `stg_erp_customers`
- Core target: `CORE.DIM_CUSTOMER`
- Business key: `customer_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `customer_id` | `string` | No | PK | — | Stable customer business identifier. |
| `customer_name` | `string` | No | — | — | Fictional organisation name. |
| `industry` | `string` | No | — | `ENERGY`, `CHEMICALS`, `MANUFACTURING`, `MINING`, `UTILITIES` | Customer industry grouping. |
| `customer_region` | `string` | No | — | `NORTH`, `SOUTH`, `EAST`, `WEST`, `CENTRAL` | Commercial region assigned to the customer. |
| `customer_status` | `string` | No | — | `ACTIVE`, `INACTIVE` | Current customer status. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the source record was created. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## sites

- Source area: ERP
- Source file: `sites.csv`
- Raw table: `RAW.ERP_SITES`
- Staging model: `stg_erp_sites`
- Core target: `CORE.DIM_SITE`
- Business key: `site_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `site_id` | `string` | No | PK | — | Stable site business identifier. |
| `customer_id` | `string` | No | FK to `customers.customer_id` | — | Customer that owns or operates the site. |
| `site_name` | `string` | No | — | — | Fictional site name. |
| `country_code` | `string` | No | — | — | Uppercase two-letter country code. |
| `region` | `string` | No | — | `NORTH`, `SOUTH`, `EAST`, `WEST`, `CENTRAL` | Operational service region. |
| `timezone` | `string` | No | — | — | IANA-style time-zone name for the site. |
| `site_status` | `string` | No | — | `ACTIVE`, `INACTIVE` | Current site status. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the source record was created. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## assets

- Source area: ERP
- Source file: `assets.csv`
- Raw table: `RAW.ERP_ASSETS`
- Staging model: `stg_erp_assets`
- Core target: `CORE.DIM_ASSET`
- Business key: `asset_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `asset_id` | `string` | No | PK | — | Stable asset business identifier. |
| `site_id` | `string` | No | FK to `sites.site_id` | — | Site where the asset is installed. |
| `asset_name` | `string` | No | — | — | Readable asset label. |
| `asset_type` | `string` | No | — | `GAS_TURBINE`, `STEAM_TURBINE`, `COMPRESSOR`, `INDUSTRIAL_PUMP` | Controlled equipment type. |
| `manufacturer` | `string` | No | — | — | Fictional equipment manufacturer. |
| `model` | `string` | No | — | — | Equipment model designation. |
| `serial_number` | `string` | No | — | — | Unique source serial number. |
| `installation_date` | `date` | No | — | — | Date the asset entered service. |
| `criticality` | `string` | No | — | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Operational importance of the asset. |
| `asset_status` | `string` | No | — | `ACTIVE`, `OUT_OF_SERVICE`, `RETIRED` | Current asset lifecycle status. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the source record was created. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## service_contracts

- Source area: CRM
- Source file: `service_contracts.csv`
- Raw table: `RAW.CRM_SERVICE_CONTRACTS`
- Staging model: `stg_crm_service_contracts`
- Core target: `CORE.DIM_SERVICE_CONTRACT`
- Business key: `contract_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `contract_id` | `string` | No | PK | — | Stable service-contract business identifier. |
| `customer_id` | `string` | No | FK to `customers.customer_id` | — | Customer covered by the contract. |
| `site_id` | `string` | No | FK to `sites.site_id` | — | Site covered by the contract. |
| `contract_type` | `string` | No | — | `BASIC`, `STANDARD`, `PREMIUM` | Service coverage level. |
| `start_date` | `date` | No | — | — | Contract start date. |
| `end_date` | `date` | No | — | — | Contract end date. |
| `response_sla_hours` | `integer` | No | — | — | Allowed elapsed hours to first response. |
| `resolution_sla_hours` | `integer` | No | — | — | Allowed elapsed hours to case resolution. |
| `contract_status` | `string` | No | — | `DRAFT`, `ACTIVE`, `EXPIRED`, `CANCELLED` | Current contract status. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the source record was created. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## customer_cases

- Source area: CRM
- Source file: `customer_cases.csv`
- Raw table: `RAW.CRM_CUSTOMER_CASES`
- Staging model: `stg_crm_customer_cases`
- Core target: `CORE.FACT_SERVICE_CASE`
- Business key: `case_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `case_id` | `string` | No | PK | — | Stable case business identifier. |
| `customer_id` | `string` | No | FK to `customers.customer_id` | — | Customer that raised the case. |
| `site_id` | `string` | No | FK to `sites.site_id` | — | Site associated with the case. |
| `contract_id` | `string` | Yes | FK to `service_contracts.contract_id` | — | Applicable service contract when one exists. |
| `asset_id` | `string` | Yes | FK to `assets.asset_id` | — | Asset associated with the case when relevant. |
| `case_type` | `string` | No | — | `TECHNICAL_FAULT`, `INSPECTION_REQUEST`, `MAINTENANCE_REQUEST`, `GENERAL_ENQUIRY` | Reason the case was opened. |
| `priority` | `string` | No | — | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | Operational priority assigned to the case. |
| `fault_category` | `string` | Yes | — | `BEARING`, `VIBRATION`, `OVERHEATING`, `LUBRICATION`, `SEAL`, `ELECTRICAL`, `CONTROL_SYSTEM`, `PRESSURE`, `FLOW`, `INSPECTION`, `OTHER` | Controlled fault category when the case concerns equipment. |
| `case_status` | `string` | No | — | `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `WAITING_PARTS`, `RESOLVED`, `CLOSED`, `CANCELLED` | Current case status. |
| `created_at` | `timestamp_utc` | No | — | — | Case creation timestamp. |
| `response_due_at` | `timestamp_utc` | No | — | — | Deadline for the first response. |
| `resolution_due_at` | `timestamp_utc` | No | — | — | Deadline for case resolution. |
| `first_response_at` | `timestamp_utc` | Yes | — | — | Timestamp of the first recorded response. |
| `resolved_at` | `timestamp_utc` | Yes | — | — | Timestamp of the first valid resolution. |
| `closed_at` | `timestamp_utc` | Yes | — | — | Timestamp when the case was closed. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## case_status_history

- Source area: CRM
- Source file: `case_status_history.csv`
- Raw table: `RAW.CRM_CASE_STATUS_HISTORY`
- Staging model: `stg_crm_case_status_history`
- Core target: `CORE.FACT_CASE_STATUS_EVENT`
- Business key: `case_status_event_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `case_status_event_id` | `string` | No | PK | — | Stable status-event business identifier. |
| `case_id` | `string` | No | FK to `customer_cases.case_id` | — | Case affected by the status change. |
| `previous_status` | `string` | Yes | — | `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `WAITING_PARTS`, `RESOLVED`, `CLOSED`, `CANCELLED` | Status before the change; null for the first event. |
| `new_status` | `string` | No | — | `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `WAITING_PARTS`, `RESOLVED`, `CLOSED`, `CANCELLED` | Status after the change. |
| `changed_at` | `timestamp_utc` | No | — | — | Timestamp when the status changed. |
| `change_reason` | `string` | No | — | — | Short explanation recorded with the transition. |

## technicians

- Source area: ERP
- Source file: `technicians.csv`
- Raw table: `RAW.ERP_TECHNICIANS`
- Staging model: `stg_erp_technicians`
- Core target: `CORE.DIM_TECHNICIAN`
- Business key: `technician_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `technician_id` | `string` | No | PK | — | Stable technician business identifier. |
| `technician_name` | `string` | No | — | — | Fictional technician name. |
| `home_region` | `string` | No | — | `NORTH`, `SOUTH`, `EAST`, `WEST`, `CENTRAL` | Technician's normal service region. |
| `specialisation` | `string` | No | — | `ROTATING_EQUIPMENT`, `ELECTRICAL`, `CONTROLS`, `INSTRUMENTATION`, `GENERAL` | Primary technical specialisation. |
| `skill_level` | `string` | No | — | `JUNIOR`, `INTERMEDIATE`, `SENIOR`, `EXPERT` | Experience band used for generated assignments. |
| `technician_status` | `string` | No | — | `ACTIVE`, `INACTIVE` | Current technician status. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the source record was created. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## service_orders

- Source area: ERP
- Source file: `service_orders.csv`
- Raw table: `RAW.ERP_SERVICE_ORDERS`
- Staging model: `stg_erp_service_orders`
- Core target: `CORE.FACT_SERVICE_ORDER`
- Business key: `service_order_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `service_order_id` | `string` | No | PK | — | Stable service-order business identifier. |
| `case_id` | `string` | Yes | FK to `customer_cases.case_id` | — | Related customer case when the order is reactive. |
| `asset_id` | `string` | No | FK to `assets.asset_id` | — | Asset receiving the service work. |
| `lead_technician_id` | `string` | No | FK to `technicians.technician_id` | — | Lead technician assigned to the order. |
| `order_type` | `string` | No | — | `INSPECTION`, `CORRECTIVE_REPAIR`, `PREVENTIVE_MAINTENANCE`, `EMERGENCY_REPAIR` | Type of service activity. |
| `order_status` | `string` | No | — | `PLANNED`, `DISPATCHED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED` | Current service-order status. |
| `created_at` | `timestamp_utc` | No | — | — | Service-order creation timestamp. |
| `scheduled_start_at` | `timestamp_utc` | No | — | — | Planned start timestamp. |
| `actual_start_at` | `timestamp_utc` | Yes | — | — | Actual start timestamp when work has begun. |
| `completed_at` | `timestamp_utc` | Yes | — | — | Completion timestamp for completed work. |
| `downtime_start_at` | `timestamp_utc` | Yes | — | — | Start of the associated equipment downtime interval. |
| `downtime_end_at` | `timestamp_utc` | Yes | — | — | End of the associated equipment downtime interval. |
| `resolution_code` | `string` | Yes | — | `FIXED`, `ADJUSTED`, `REPLACED_COMPONENT`, `NO_FAULT_FOUND`, `FOLLOW_UP_REQUIRED`, `NOT_COMPLETED` | Outcome recorded when the order is completed. |
| `created_by_source` | `string` | No | — | `CRM_CASE`, `PLANNED_MAINTENANCE`, `MONITORING_ALERT` | Source process that created the service order. |

## parts

- Source area: ERP
- Source file: `parts.csv`
- Raw table: `RAW.ERP_PARTS`
- Staging model: `stg_erp_parts`
- Core target: `CORE.DIM_PART`
- Business key: `part_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `part_id` | `string` | No | PK | — | Stable part business identifier. |
| `part_name` | `string` | No | — | — | Fictional spare-part name. |
| `part_category` | `string` | No | — | `BEARING`, `SEAL`, `LUBRICATION`, `ELECTRICAL`, `CONTROL`, `VALVE`, `FILTER`, `FASTENER`, `OTHER` | Controlled spare-part category. |
| `unit_cost_eur` | `decimal_18_2` | No | — | — | Standard unit cost in EUR. |
| `standard_lead_time_days` | `integer` | No | — | — | Expected supplier lead time in elapsed days. |
| `part_status` | `string` | No | — | `ACTIVE`, `OBSOLETE` | Current part status. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the source record was created. |
| `updated_at` | `timestamp_utc` | No | — | — | Timestamp of the latest source update. |

## service_order_parts

- Source area: ERP
- Source file: `service_order_parts.csv`
- Raw table: `RAW.ERP_SERVICE_ORDER_PARTS`
- Staging model: `stg_erp_service_order_parts`
- Core target: `CORE.FACT_SERVICE_ORDER_PART`
- Business key: `service_order_id`, `part_id`, `line_number`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `service_order_id` | `string` | No | PK, FK to `service_orders.service_order_id` | — | Service order that requested or used the part. |
| `part_id` | `string` | No | PK, FK to `parts.part_id` | — | Requested or consumed part. |
| `line_number` | `integer` | No | PK | — | Line number unique within the order and part combination. |
| `quantity` | `integer` | No | — | — | Positive quantity requested. |
| `requested_at` | `timestamp_utc` | No | — | — | Timestamp when the part was requested. |
| `required_at` | `timestamp_utc` | No | — | — | Timestamp by which the part was required. |
| `delivered_at` | `timestamp_utc` | Yes | — | — | Actual delivery timestamp; null while outstanding. |
| `unit_cost_eur` | `decimal_18_2` | No | — | — | Unit cost recorded on the service-order line. |

## service_costs

- Source area: ERP
- Source file: `service_costs.csv`
- Raw table: `RAW.ERP_SERVICE_COSTS`
- Staging model: `stg_erp_service_costs`
- Core target: `CORE.FACT_SERVICE_COST`
- Business key: `service_cost_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `service_cost_id` | `string` | No | PK | — | Stable service-cost transaction identifier. |
| `service_order_id` | `string` | No | FK to `service_orders.service_order_id` | — | Service order receiving the cost. |
| `cost_type` | `string` | No | — | `LABOUR`, `TRAVEL`, `PART`, `EXTERNAL_SERVICE` | Type of service expenditure. |
| `cost_amount_eur` | `decimal_18_2` | No | — | — | Transaction amount in EUR. |
| `cost_recorded_at` | `timestamp_utc` | No | — | — | Timestamp when the cost was recorded. |

## equipment_alerts

- Source area: Monitoring
- Source file: `equipment_alerts.csv`
- Raw table: `RAW.MONITORING_EQUIPMENT_ALERTS`
- Staging model: `stg_monitoring_equipment_alerts`
- Core target: `CORE.FACT_EQUIPMENT_ALERT`
- Business key: `alert_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `alert_id` | `string` | No | PK | — | Stable alert business identifier. |
| `asset_id` | `string` | No | FK to `assets.asset_id` | — | Asset that generated the alert. |
| `related_case_id` | `string` | Yes | FK to `customer_cases.case_id` | — | Customer case explicitly linked to the alert. |
| `alert_type` | `string` | No | — | `VIBRATION`, `TEMPERATURE`, `PRESSURE`, `FLOW`, `LUBRICATION`, `ELECTRICAL`, `CONTROL_SYSTEM` | Condition represented by the alert. |
| `severity` | `string` | No | — | `INFO`, `WARNING`, `CRITICAL` | Operational severity of the alert. |
| `alert_status` | `string` | No | — | `OPEN`, `ACKNOWLEDGED`, `CLEARED` | Current alert state. |
| `raised_at` | `timestamp_utc` | No | — | — | Timestamp when the alert was raised. |
| `acknowledged_at` | `timestamp_utc` | Yes | — | — | Timestamp of manual or automatic acknowledgement. |
| `cleared_at` | `timestamp_utc` | Yes | — | — | Timestamp when the alert was cleared. |
| `measured_value` | `decimal_18_6` | Yes | — | — | Measured value when the alert is numeric. |
| `threshold_value` | `decimal_18_6` | Yes | — | — | Configured threshold when the alert is numeric. |
| `measurement_unit` | `string` | Yes | — | — | Unit used for measured and threshold values. |

## technician_notes

- Source area: Field service
- Source file: `technician_notes.csv`
- Raw table: `RAW.FIELD_SERVICE_TECHNICIAN_NOTES`
- Staging model: `stg_field_service_technician_notes`
- Core target: `CORE.FACT_TECHNICIAN_NOTE`
- Business key: `note_id`

| Field | Type | Nullable | Key or reference | Allowed values | Description |
|---|---|---:|---|---|---|
| `note_id` | `string` | No | PK | — | Stable note business identifier. |
| `service_order_id` | `string` | No | FK to `service_orders.service_order_id` | — | Service order documented by the note. |
| `technician_id` | `string` | No | FK to `technicians.technician_id` | — | Technician who authored the note. |
| `note_type` | `string` | No | — | `INSPECTION`, `DIAGNOSIS`, `REPAIR`, `COMPLETION` | Stage of field work represented by the note. |
| `note_text` | `string` | No | — | — | Original free-text field-service observation. |
| `created_at` | `timestamp_utc` | No | — | — | Timestamp when the note was created. |
