# Conceptual data model

## Purpose

The model connects customer service activity with the industrial assets being maintained. It is intentionally smaller than a real ERP or CRM model, but it keeps the relationships needed to calculate service, reliability, downtime, cost, and SLA metrics.

The source data will preserve business identifiers such as `CASE-000001` and `ASSET-000001`. Snowflake dimensions will later receive separate surrogate keys so that historical changes can be handled without replacing the source identifiers.

## Source systems

| Source area | Responsibility |
|---|---|
| ERP | Customers, sites, assets, service orders, technicians, parts, and service costs |
| CRM | Customer cases, case history, and service contracts |
| Monitoring | Equipment alerts |
| Field service | Technician notes |

## Core entities

| Entity | Business identifier | Source area | Purpose |
|---|---|---|---|
| Customer | `customer_id` | ERP | Organisation receiving equipment service |
| Site | `site_id` | ERP | Physical customer location |
| Asset | `asset_id` | ERP | Individual item of industrial equipment |
| Service contract | `contract_id` | CRM | Agreement defining service coverage and SLA terms |
| Customer case | `case_id` | CRM | Customer-reported issue or service request |
| Case status history | `case_status_event_id` | CRM | Timestamped record of case-status changes |
| Service order | `service_order_id` | ERP | Planned or completed field-service activity |
| Technician | `technician_id` | ERP | Lead technician assigned to a service order |
| Part | `part_id` | ERP | Spare part that may be used during service |
| Service-order part | Composite key | ERP | Quantity and delivery information for a part used by an order |
| Service cost | `service_cost_id` | ERP | Labour, travel, part, or external cost recorded against an order |
| Equipment alert | `alert_id` | Monitoring | Operational or condition-related alert generated for an asset |
| Technician note | `note_id` | Field service | Free-text inspection or repair observation |

## Entity details

### Customer

A customer is an organisation that owns or operates one or more sites.

Required fields:

- `customer_id`
- `customer_name`
- `industry`
- `customer_region`
- `customer_status`
- `created_at`
- `updated_at`

Allowed status values:

- `ACTIVE`
- `INACTIVE`

### Site

A site is a physical customer location at which assets are installed.

Required fields:

- `site_id`
- `customer_id`
- `site_name`
- `country_code`
- `region`
- `timezone`
- `site_status`
- `created_at`
- `updated_at`

Allowed status values:

- `ACTIVE`
- `INACTIVE`

### Asset

An asset is an individually tracked piece of equipment.

Required fields:

- `asset_id`
- `site_id`
- `asset_name`
- `asset_type`
- `manufacturer`
- `model`
- `serial_number`
- `installation_date`
- `criticality`
- `asset_status`
- `created_at`
- `updated_at`

Initial asset types:

- `GAS_TURBINE`
- `STEAM_TURBINE`
- `COMPRESSOR`
- `INDUSTRIAL_PUMP`

Allowed criticality values:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Allowed status values:

- `ACTIVE`
- `OUT_OF_SERVICE`
- `RETIRED`

### Service contract

A service contract belongs to one customer and covers one site.

Required fields:

- `contract_id`
- `customer_id`
- `site_id`
- `contract_type`
- `start_date`
- `end_date`
- `response_sla_hours`
- `resolution_sla_hours`
- `contract_status`
- `created_at`
- `updated_at`

Allowed contract types:

- `BASIC`
- `STANDARD`
- `PREMIUM`

Allowed status values:

- `DRAFT`
- `ACTIVE`
- `EXPIRED`
- `CANCELLED`

An active contract must have a start date on or before the current record date and an end date after its start date.

### Customer case

A customer case represents a reported issue or request.

Required fields:

- `case_id`
- `customer_id`
- `site_id`
- `contract_id`
- `asset_id`
- `case_type`
- `priority`
- `fault_category`
- `case_status`
- `created_at`
- `response_due_at`
- `resolution_due_at`
- `first_response_at`
- `resolved_at`
- `closed_at`
- `updated_at`

`asset_id` may be empty for a non-equipment enquiry. Technical fault cases should normally reference an asset.

Allowed case types:

- `TECHNICAL_FAULT`
- `INSPECTION_REQUEST`
- `MAINTENANCE_REQUEST`
- `GENERAL_ENQUIRY`

Allowed priorities:

- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

Allowed status values:

- `OPEN`
- `ASSIGNED`
- `IN_PROGRESS`
- `WAITING_PARTS`
- `RESOLVED`
- `CLOSED`
- `CANCELLED`

### Case status history

Each status change for a customer case is stored as a separate event.

Required fields:

- `case_status_event_id`
- `case_id`
- `previous_status`
- `new_status`
- `changed_at`
- `change_reason`

The first event has no previous status and must set the case to `OPEN`.

### Service order

A service order records an inspection, repair, or maintenance visit.

Required fields:

- `service_order_id`
- `case_id`
- `asset_id`
- `lead_technician_id`
- `order_type`
- `order_status`
- `created_at`
- `scheduled_start_at`
- `actual_start_at`
- `completed_at`
- `downtime_start_at`
- `downtime_end_at`
- `resolution_code`
- `created_by_source`

A service order may exist without a customer case when it represents planned maintenance. Every order must reference an asset.

Allowed order types:

- `INSPECTION`
- `CORRECTIVE_REPAIR`
- `PREVENTIVE_MAINTENANCE`
- `EMERGENCY_REPAIR`

Allowed status values:

- `PLANNED`
- `DISPATCHED`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`

### Technician

A technician is the lead field-service worker assigned to a service order.

Required fields:

- `technician_id`
- `technician_name`
- `home_region`
- `specialisation`
- `skill_level`
- `technician_status`
- `created_at`
- `updated_at`

Allowed status values:

- `ACTIVE`
- `INACTIVE`

### Part

A part is an item that may be requested or consumed during service.

Required fields:

- `part_id`
- `part_name`
- `part_category`
- `unit_cost_eur`
- `standard_lead_time_days`
- `part_status`
- `created_at`
- `updated_at`

Allowed status values:

- `ACTIVE`
- `OBSOLETE`

### Service-order part

This entity connects service orders and parts.

Composite business key:

- `service_order_id`
- `part_id`
- `line_number`

Required fields:

- `service_order_id`
- `part_id`
- `line_number`
- `quantity`
- `requested_at`
- `required_at`
- `delivered_at`
- `unit_cost_eur`

A service order may use the same part on more than one line, so `line_number` is included in the key.

### Service cost

A service order can contain several cost records.

Required fields:

- `service_cost_id`
- `service_order_id`
- `cost_type`
- `cost_amount_eur`
- `cost_recorded_at`

Allowed cost types:

- `LABOUR`
- `TRAVEL`
- `PART`
- `EXTERNAL_SERVICE`

### Equipment alert

An equipment alert is raised against one asset.

Required fields:

- `alert_id`
- `asset_id`
- `related_case_id`
- `alert_type`
- `severity`
- `alert_status`
- `raised_at`
- `acknowledged_at`
- `cleared_at`
- `measured_value`
- `threshold_value`
- `measurement_unit`

`related_case_id` is optional because not every monitoring alert becomes a customer case.

Allowed severity values:

- `INFO`
- `WARNING`
- `CRITICAL`

Allowed status values:

- `OPEN`
- `ACKNOWLEDGED`
- `CLEARED`

### Technician note

A technician note belongs to one service order and inherits its case and asset context.

Required fields:

- `note_id`
- `service_order_id`
- `technician_id`
- `note_type`
- `note_text`
- `created_at`

Allowed note types:

- `INSPECTION`
- `DIAGNOSIS`
- `REPAIR`
- `COMPLETION`

Structured fault category, component, priority, summary, and recommended team fields will be produced later by the enrichment step. They are not part of the original note source.

## Relationships

| Parent | Child | Cardinality | Rule |
|---|---|---|---|
| Customer | Site | One to many | Every site belongs to exactly one customer |
| Customer | Service contract | One to many | Every contract belongs to exactly one customer |
| Site | Service contract | One to many | Every contract covers exactly one site |
| Site | Asset | One to many | Every asset belongs to exactly one site |
| Customer | Customer case | One to many | Every case belongs to exactly one customer |
| Site | Customer case | One to many | Every case belongs to exactly one site |
| Service contract | Customer case | One to many | A case may reference one applicable contract |
| Asset | Customer case | One to many | A case may reference one asset |
| Customer case | Case status history | One to many | Every case has one or more status events |
| Customer case | Service order | One to many | A case may produce zero or more orders |
| Asset | Service order | One to many | Every service order belongs to one asset |
| Technician | Service order | One to many | Every order has one lead technician |
| Service order | Service-order part | One to many | An order may use zero or more part lines |
| Part | Service-order part | One to many | A part may appear on many order lines |
| Service order | Service cost | One to many | An order may have zero or more cost records |
| Asset | Equipment alert | One to many | Every alert belongs to one asset |
| Customer case | Equipment alert | One to many | An alert may optionally reference one case |
| Service order | Technician note | One to many | An order may contain zero or more notes |
| Technician | Technician note | One to many | Every note is authored by one technician |

## Lifecycle rules

### Customer case lifecycle

Normal progression:

    OPEN
      |
    ASSIGNED
      |
    IN_PROGRESS
      | \
      |  WAITING_PARTS
      |       |
      +-------+
      |
    RESOLVED
      |
    CLOSED

A case may move to `CANCELLED` from `OPEN`, `ASSIGNED`, or `IN_PROGRESS`.

A resolved case may be reopened by returning to `IN_PROGRESS`. The status-history table must retain both the original resolution and the reopening event.

### Service-order lifecycle

Normal progression:

    PLANNED
       |
    DISPATCHED
       |
    IN_PROGRESS
       |
    COMPLETED

An order may move to `CANCELLED` before completion.

### Equipment-alert lifecycle

Normal progression:

    OPEN
      |
    ACKNOWLEDGED
      |
    CLEARED

An alert may be cleared directly from `OPEN` when no manual acknowledgement is required.

### Asset lifecycle

Normal progression:

    ACTIVE
      |
    OUT_OF_SERVICE
      |
    ACTIVE

An asset may eventually move from `ACTIVE` or `OUT_OF_SERVICE` to `RETIRED`. A retired asset cannot return to active service in the generated source data.

## Timestamp rules

- All timestamps are stored in UTC.
- `created_at` must not occur after `updated_at`.
- A site's creation date must not precede its customer's creation date.
- An asset's installation date must not occur after its first case, alert, or service order.
- `response_due_at` and `resolution_due_at` must occur after case creation.
- `first_response_at` must not occur before case creation.
- `resolved_at` must not occur before case creation.
- `closed_at` must not occur before `resolved_at`.
- `scheduled_start_at` must not occur before service-order creation.
- `actual_start_at` must not occur before service-order creation.
- `completed_at` must not occur before `actual_start_at`.
- `downtime_end_at` must not occur before `downtime_start_at`.
- `delivered_at` must not occur before a part was requested.
- `acknowledged_at` must not occur before an alert was raised.
- `cleared_at` must not occur before an alert was raised.
- A technician note must not predate its service order.

## Financial rules

- All monetary values are stored in EUR.
- Part quantities must be positive integers.
- Unit costs and service costs must be non-negative.
- Extended part cost is calculated as quantity multiplied by unit cost.
- Total service-order cost is derived from cost records rather than stored as an independent source field.

## Identifier rules

Business identifiers use stable prefixes:

| Entity | Format |
|---|---|
| Customer | `CUST-000001` |
| Site | `SITE-000001` |
| Asset | `ASSET-000001` |
| Contract | `CONT-000001` |
| Customer case | `CASE-000001` |
| Case status event | `CSEVT-000001` |
| Service order | `SORD-000001` |
| Technician | `TECH-000001` |
| Part | `PART-000001` |
| Service cost | `COST-000001` |
| Equipment alert | `ALERT-000001` |
| Technician note | `NOTE-000001` |

Identifiers are strings and are never reused. Records loaded more than once with the same source identifier must update or be ignored according to the later ingestion rules; they must not create duplicate business records.

## Historical handling

The source datasets contain the latest customer, site, technician, and part records.

Asset changes are different because site assignment, criticality, and service status may affect historical reporting. The Snowflake model will therefore preserve asset history through a dbt snapshot and a slowly changing dimension.

Case statuses are already event-based and do not require a dimensional snapshot.

## Deliberate simplifications

The first version uses one lead technician per service order. A real field-service system may assign a team.

A contract covers one site rather than maintaining a separate contract-to-asset coverage table.

Currency conversion is excluded because all generated costs use EUR.

Parts inventory, purchase orders, invoicing, and technician scheduling are outside the model.

These choices keep the project focused on data integration and service analytics rather than reproducing an entire enterprise application.
