# Source-to-target mapping

## Purpose

This document describes how the generated ERP-, CRM-, monitoring-, and field-service datasets will move through the platform.

The mapping is defined before implementation so that source generation, ingestion, dbt models, analytical tables, and Power BI measures use the same field names and relationships.

## Data layers

| Layer | Responsibility |
|---|---|
| Source files | Generated CSV or JSON files shaped like operational-system exports |
| `RAW` | Source values preserved with ingestion metadata |
| `STAGING` | Typed, renamed, deduplicated, and validated source records |
| `CORE` | Integrated dimensions, facts, histories, and reusable business logic |
| `ANALYTICS` | Reporting marts and KPI-ready datasets |
| `OPERATIONS` | Pipeline runs, rejected records, test results, and processing history |

## Naming conventions

### Source files

Source files use lowercase snake case:

- `customers.csv`
- `sites.csv`
- `assets.csv`
- `service_contracts.csv`
- `customer_cases.csv`
- `case_status_history.csv`
- `service_orders.csv`
- `technicians.csv`
- `parts.csv`
- `service_order_parts.csv`
- `service_costs.csv`
- `equipment_alerts.csv`
- `technician_notes.csv`

### Snowflake raw tables

Raw tables use uppercase names containing the source area:

- `RAW.ERP_CUSTOMERS`
- `RAW.CRM_CUSTOMER_CASES`
- `RAW.MONITORING_EQUIPMENT_ALERTS`
- `RAW.FIELD_SERVICE_TECHNICIAN_NOTES`

### dbt staging models

Staging models use lowercase snake case and the `stg_` prefix:

- `stg_erp_customers`
- `stg_crm_customer_cases`
- `stg_monitoring_equipment_alerts`

### Core models

Reusable integrated models use dimensional or fact-style names:

- `dim_customer`
- `dim_site`
- `dim_asset`
- `fact_service_case`
- `fact_service_order`

### Analytical marts

Reporting models use the `mart_` prefix:

- `mart_service_operations`
- `mart_asset_reliability`
- `mart_customer_performance`
- `mart_parts_delay`
- `mart_technician_note_enrichment`

## Raw ingestion metadata

Every raw table receives the following technical fields in addition to its source columns:

| Field | Type | Purpose |
|---|---|---|
| `_load_batch_id` | `VARCHAR` | Identifier shared by records loaded in the same batch |
| `_source_system` | `VARCHAR` | ERP, CRM, monitoring, or field service |
| `_source_file_name` | `VARCHAR` | Name of the source file |
| `_source_row_number` | `NUMBER` | Original row position in the file |
| `_ingested_at` | `TIMESTAMP_TZ` | Time the record reached Snowflake |
| `_record_hash` | `VARCHAR` | Hash used to detect repeated source content |

These fields are not business attributes and must not appear as Power BI dimensions.

## Source table mapping

| Source area | Source dataset | Raw table | Staging model | Main core target |
|---|---|---|---|---|
| ERP | `customers` | `RAW.ERP_CUSTOMERS` | `stg_erp_customers` | `CORE.DIM_CUSTOMER` |
| ERP | `sites` | `RAW.ERP_SITES` | `stg_erp_sites` | `CORE.DIM_SITE` |
| ERP | `assets` | `RAW.ERP_ASSETS` | `stg_erp_assets` | `CORE.DIM_ASSET` |
| ERP | `service_orders` | `RAW.ERP_SERVICE_ORDERS` | `stg_erp_service_orders` | `CORE.FACT_SERVICE_ORDER` |
| ERP | `technicians` | `RAW.ERP_TECHNICIANS` | `stg_erp_technicians` | `CORE.DIM_TECHNICIAN` |
| ERP | `parts` | `RAW.ERP_PARTS` | `stg_erp_parts` | `CORE.DIM_PART` |
| ERP | `service_order_parts` | `RAW.ERP_SERVICE_ORDER_PARTS` | `stg_erp_service_order_parts` | `CORE.FACT_SERVICE_ORDER_PART` |
| ERP | `service_costs` | `RAW.ERP_SERVICE_COSTS` | `stg_erp_service_costs` | `CORE.FACT_SERVICE_COST` |
| CRM | `service_contracts` | `RAW.CRM_SERVICE_CONTRACTS` | `stg_crm_service_contracts` | `CORE.DIM_SERVICE_CONTRACT` |
| CRM | `customer_cases` | `RAW.CRM_CUSTOMER_CASES` | `stg_crm_customer_cases` | `CORE.FACT_SERVICE_CASE` |
| CRM | `case_status_history` | `RAW.CRM_CASE_STATUS_HISTORY` | `stg_crm_case_status_history` | `CORE.FACT_CASE_STATUS_EVENT` |
| Monitoring | `equipment_alerts` | `RAW.MONITORING_EQUIPMENT_ALERTS` | `stg_monitoring_equipment_alerts` | `CORE.FACT_EQUIPMENT_ALERT` |
| Field service | `technician_notes` | `RAW.FIELD_SERVICE_TECHNICIAN_NOTES` | `stg_field_service_technician_notes` | `CORE.FACT_TECHNICIAN_NOTE` |

## Customer mapping

### Source

`customers.csv`

### Business key

`customer_id`

### Target flow

    customers.csv
        -> RAW.ERP_CUSTOMERS
        -> stg_erp_customers
        -> CORE.DIM_CUSTOMER

### Staging rules

- Trim surrounding whitespace.
- Convert identifiers and category fields to uppercase where appropriate.
- Parse `created_at` and `updated_at` as UTC timestamps.
- Reject missing `customer_id` or `customer_name`.
- Reject unsupported customer-status values.
- Retain the latest valid row when duplicate identifiers occur in one batch.

### Core handling

`DIM_CUSTOMER` stores one current row per customer. A surrogate `customer_key` is created for analytical joins while `customer_id` remains available for traceability.

## Site mapping

### Source

`sites.csv`

### Business key

`site_id`

### Target flow

    sites.csv
        -> RAW.ERP_SITES
        -> stg_erp_sites
        -> CORE.DIM_SITE

### Staging rules

- Require a valid `customer_id`.
- Standardise country codes to uppercase ISO-style values.
- Parse timestamps as UTC.
- Reject missing time zones.
- Reject sites whose customer does not exist after source integration.
- Standardise region labels through a controlled mapping.

### Core handling

`DIM_SITE` receives a surrogate `site_key` and a `customer_key`.

## Asset mapping

### Source

`assets.csv`

### Business key

`asset_id`

### Target flow

    assets.csv
        -> RAW.ERP_ASSETS
        -> stg_erp_assets
        -> asset snapshot
        -> CORE.DIM_ASSET

### Staging rules

- Require a valid `site_id`.
- Standardise asset type, criticality, and status.
- Parse installation dates separately from timestamps.
- Reject duplicate serial numbers when both records represent active assets.
- Reject installation dates after the ingestion timestamp.
- Reject unsupported asset-type or criticality values.

### Historical handling

The asset snapshot tracks changes to:

- site assignment;
- asset criticality;
- asset status;
- model;
- manufacturer.

The dimensional target contains:

- `asset_key`;
- source `asset_id`;
- valid-from timestamp;
- valid-to timestamp;
- current-row flag.

Historical service events join to the asset version valid at the event timestamp.

## Service contract mapping

### Source

`service_contracts.csv`

### Business key

`contract_id`

### Target flow

    service_contracts.csv
        -> RAW.CRM_SERVICE_CONTRACTS
        -> stg_crm_service_contracts
        -> CORE.DIM_SERVICE_CONTRACT

### Staging rules

- Require valid customer and site identifiers.
- Confirm that the site belongs to the referenced customer.
- Require positive response and resolution SLA hours.
- Reject an end date before the start date.
- Standardise contract type and status.
- Mark overlapping active contracts for the same site for review.

### Core handling

The dimension stores contract dates, SLA terms, status, customer key, and site key.

## Customer case mapping

### Source

`customer_cases.csv`

### Business key

`case_id`

### Target flow

    customer_cases.csv
        -> RAW.CRM_CUSTOMER_CASES
        -> stg_crm_customer_cases
        -> intermediate SLA and resolution models
        -> CORE.FACT_SERVICE_CASE

### Staging rules

- Require valid customer and site identifiers.
- Confirm that the site belongs to the referenced customer.
- Validate optional contract and asset references.
- Standardise case type, priority, fault category, and status.
- Parse all timestamps as UTC.
- Reject impossible timestamp sequences.
- Require `resolved_at` for resolved or closed cases.
- Require `closed_at` for closed cases.
- Permit a null asset only for cases where equipment context is not required.

### Core handling

`FACT_SERVICE_CASE` stores one current row per case with foreign keys to customer, site, asset, contract, date, and fault-category dimensions.

Derived fields include:

- response duration hours;
- resolution duration hours;
- response SLA outcome;
- resolution SLA outcome;
- backlog age;
- current open-case flag.

Reporting-time-dependent fields are calculated in analytical models using `reporting_as_of`.

## Case status history mapping

### Source

`case_status_history.csv`

### Business key

`case_status_event_id`

### Target flow

    case_status_history.csv
        -> RAW.CRM_CASE_STATUS_HISTORY
        -> stg_crm_case_status_history
        -> CORE.FACT_CASE_STATUS_EVENT

### Staging rules

- Require a valid case identifier.
- Parse `changed_at` as UTC.
- Validate previous and new statuses.
- Require the first status event for each case to move to `OPEN`.
- Reject an event timestamp before case creation.
- Detect contradictory transitions while preserving rejected records for review.

### Core handling

The fact table retains every valid status transition and supports reopening, waiting-time, and lifecycle analysis.

## Service order mapping

### Source

`service_orders.csv`

### Business key

`service_order_id`

### Target flow

    service_orders.csv
        -> RAW.ERP_SERVICE_ORDERS
        -> stg_erp_service_orders
        -> intermediate duration and downtime models
        -> CORE.FACT_SERVICE_ORDER

### Staging rules

- Require valid asset and technician identifiers.
- Validate an optional case reference.
- Standardise order type, status, and resolution code.
- Parse timestamps as UTC.
- Reject completion before actual start.
- Reject downtime end before downtime start.
- Require completion information for completed orders.
- Permit planned-maintenance orders without a case.

### Core handling

`FACT_SERVICE_ORDER` stores service timing, status, resolution, asset, case, technician, and downtime information.

Derived fields include:

- service-order duration;
- completed-order flag;
- emergency-repair flag;
- downtime duration before overlap correction.

## Technician mapping

### Source

`technicians.csv`

### Business key

`technician_id`

### Target flow

    technicians.csv
        -> RAW.ERP_TECHNICIANS
        -> stg_erp_technicians
        -> CORE.DIM_TECHNICIAN

### Staging rules

- Require technician name and home region.
- Standardise specialisation, skill level, and status.
- Parse timestamps as UTC.
- Reject unsupported status values.

### Core handling

The dimension stores one current row per technician. Personnel information is fictional and limited to fields needed for service analysis.

## Part mapping

### Source

`parts.csv`

### Business key

`part_id`

### Target flow

    parts.csv
        -> RAW.ERP_PARTS
        -> stg_erp_parts
        -> CORE.DIM_PART

### Staging rules

- Require a name and category.
- Convert costs to fixed-precision decimal values.
- Reject negative costs or lead times.
- Standardise part status.
- Retain obsolete parts so historical service records remain valid.

## Service-order part mapping

### Source

`service_order_parts.csv`

### Business key

The composite source key is:

- `service_order_id`;
- `part_id`;
- `line_number`.

### Target flow

    service_order_parts.csv
        -> RAW.ERP_SERVICE_ORDER_PARTS
        -> stg_erp_service_order_parts
        -> CORE.FACT_SERVICE_ORDER_PART

### Staging rules

- Require valid service-order and part identifiers.
- Require positive integer quantities.
- Reject delivery before request.
- Convert unit cost to a fixed-precision decimal value.
- Preserve undelivered part lines with a null `delivered_at`.
- Reject duplicate composite keys.

### Core handling

Derived fields include:

- extended part cost;
- part delivery delay hours;
- delayed-line flag;
- open overdue request flag.

## Service cost mapping

### Source

`service_costs.csv`

### Business key

`service_cost_id`

### Target flow

    service_costs.csv
        -> RAW.ERP_SERVICE_COSTS
        -> stg_erp_service_costs
        -> CORE.FACT_SERVICE_COST

### Staging rules

- Require a valid service-order identifier.
- Standardise cost type.
- Convert amounts to fixed-precision EUR values.
- Reject negative amounts.
- Parse `cost_recorded_at` as UTC.

### Core handling

Costs remain stored at transaction level. Service-order and case totals are calculated downstream rather than stored as competing source values.

## Equipment alert mapping

### Source

`equipment_alerts.csv`

### Business key

`alert_id`

### Target flow

    equipment_alerts.csv
        -> RAW.MONITORING_EQUIPMENT_ALERTS
        -> stg_monitoring_equipment_alerts
        -> CORE.FACT_EQUIPMENT_ALERT

### Staging rules

- Require a valid asset identifier.
- Validate an optional related case.
- Standardise alert type, severity, status, and measurement unit.
- Parse timestamps as UTC.
- Reject acknowledgement or clearance before alert creation.
- Permit missing measured values when an alert is categorical.

### Core handling

Derived fields include:

- acknowledgement duration;
- clearance duration;
- critical-alert flag;
- alert-to-case conversion flag.

## Technician note mapping

### Source

`technician_notes.csv`

### Business key

`note_id`

### Target flow

    technician_notes.csv
        -> RAW.FIELD_SERVICE_TECHNICIAN_NOTES
        -> stg_field_service_technician_notes
        -> CORE.FACT_TECHNICIAN_NOTE
        -> ANALYTICS.MART_TECHNICIAN_NOTE_ENRICHMENT

### Staging rules

- Require valid service-order and technician identifiers.
- Require non-empty note text.
- Standardise note type.
- Parse `created_at` as UTC.
- Reject notes created before their service order.
- Preserve original note text without rewriting it.

### Enrichment handling

The original note and generated enrichment remain separate.

Generated fields include:

- predicted fault category;
- predicted component;
- predicted priority;
- recommended team;
- generated summary;
- model or rule version;
- processing timestamp;
- output-validity flag;
- evaluation label where available.

## Core analytical model

| Core model | Natural grain |
|---|---|
| `DIM_CUSTOMER` | One row per current customer |
| `DIM_SITE` | One row per current site |
| `DIM_ASSET` | One row per asset version |
| `DIM_SERVICE_CONTRACT` | One row per contract |
| `DIM_TECHNICIAN` | One row per current technician |
| `DIM_PART` | One row per part |
| `DIM_DATE` | One row per calendar date |
| `DIM_FAULT_CATEGORY` | One row per controlled fault category |
| `FACT_SERVICE_CASE` | One row per customer case |
| `FACT_CASE_STATUS_EVENT` | One row per case-status transition |
| `FACT_SERVICE_ORDER` | One row per service order |
| `FACT_SERVICE_ORDER_PART` | One row per service-order part line |
| `FACT_SERVICE_COST` | One row per service cost transaction |
| `FACT_EQUIPMENT_ALERT` | One row per equipment alert |
| `FACT_TECHNICIAN_NOTE` | One row per technician note |

## Analytical marts

### `MART_SERVICE_OPERATIONS`

Natural grain:

One row per reporting date, region, priority, case type, and fault category.

Measures include:

- open cases;
- critical open cases;
- response SLA compliance;
- resolution SLA compliance;
- mean resolution time;
- median resolution time;
- first-time-fix rate;
- service cost;
- downtime.

### `MART_ASSET_RELIABILITY`

Natural grain:

One row per asset and reporting period.

Measures include:

- case count;
- repeat failure count;
- alert count;
- critical alert count;
- downtime hours;
- service cost;
- high-risk asset flag.

### `MART_CUSTOMER_PERFORMANCE`

Natural grain:

One row per customer and reporting period.

Measures include:

- active assets;
- open cases;
- critical cases;
- SLA compliance;
- downtime;
- service cost;
- active contract count.

### `MART_PARTS_DELAY`

Natural grain:

One row per service-order part line.

Measures and attributes include:

- required date;
- delivery date;
- delay hours;
- overdue status;
- associated service-order downtime;
- part category;
- customer and asset context.

### `MART_TECHNICIAN_NOTE_ENRICHMENT`

Natural grain:

One row per technician note.

Fields include:

- original note;
- predicted structured fields;
- evaluation labels;
- output validity;
- processing version;
- processing status.

## Rejected-record handling

Records rejected during Python validation are not loaded into business raw tables.

They are written to `OPERATIONS.REJECTED_RECORDS` with:

- load batch identifier;
- source system;
- source file;
- source row number;
- business identifier when available;
- rejection code;
- rejection message;
- raw record payload;
- rejection timestamp.

Examples of rejection codes include:

- `MISSING_REQUIRED_FIELD`;
- `INVALID_ENUM_VALUE`;
- `INVALID_TIMESTAMP_ORDER`;
- `UNKNOWN_FOREIGN_KEY`;
- `DUPLICATE_BUSINESS_KEY`;
- `NEGATIVE_MONETARY_VALUE`;
- `INVALID_NUMERIC_VALUE`.

A batch may finish with rejected rows and still be marked successful when the valid rows load correctly. The run record must report accepted and rejected counts separately.

## Duplicate and update handling

### Repeated source file

A repeated file with the same content must not create duplicate business records.

The ingestion pipeline checks:

- source file name;
- record hash;
- business identifier;
- load batch history.

### Updated business record

When the same business identifier arrives with changed content:

- the raw record is retained as a new ingestion event;
- the staging model selects the latest valid source version;
- dimensions update or create history according to their model;
- immutable event facts reject conflicting updates unless a correction rule is defined.

### Immutable event records

The following are treated as event records:

- case status events;
- service costs;
- equipment alerts;
- technician notes.

A repeated identifier with different content is treated as a conflict and sent for review rather than silently overwritten.

## Late-arriving records

A child record may arrive before its referenced parent because source extracts are processed separately.

The first implementation will:

1. validate format and field-level rules;
2. hold records with unresolved foreign keys in the rejected-record area;
3. use the rejection code `UNKNOWN_FOREIGN_KEY`;
4. allow the record to be retried in a later batch after the parent exists.

The pipeline will not create placeholder customers, sites, assets, cases, or service orders.

## Standard data types

| Data category | Staging type |
|---|---|
| Business identifier | `VARCHAR` |
| Category or status | `VARCHAR` |
| Timestamp | `TIMESTAMP_TZ` |
| Calendar date | `DATE` |
| Currency | `NUMBER(18, 2)` |
| Duration | `NUMBER(18, 6)` |
| Quantity | `NUMBER(18, 0)` |
| Measurement | `NUMBER(18, 6)` |
| Boolean flag | `BOOLEAN` |
| Free text | `VARCHAR` |

Raw tables may initially store source values as text. Explicit casting occurs in staging so conversion failures can be identified rather than silently coerced.

## KPI lineage summary

| KPI | Primary core source |
|---|---|
| Open case count | `FACT_SERVICE_CASE` |
| Response SLA compliance | `FACT_SERVICE_CASE` |
| Resolution SLA compliance | `FACT_SERVICE_CASE` |
| Resolution time | `FACT_SERVICE_CASE` |
| First-time-fix rate | `FACT_SERVICE_CASE` and `FACT_SERVICE_ORDER` |
| Repeat failure rate | `FACT_SERVICE_CASE` and `DIM_ASSET` |
| Downtime | `FACT_SERVICE_ORDER` |
| Part delivery delay | `FACT_SERVICE_ORDER_PART` |
| Total service cost | `FACT_SERVICE_COST` |
| Alert-to-case conversion | `FACT_EQUIPMENT_ALERT` |
| High-risk asset flag | Cases, orders, alerts, costs, and asset dimension |
| Note enrichment quality | `FACT_TECHNICIAN_NOTE` and enrichment mart |

Detailed formulas and eligibility rules are defined in `docs/kpi_catalogue.md`.

## Traceability requirements

Every analytical record must retain enough information to trace it back to:

- its source business identifier;
- the source system;
- the originating load batch;
- the dbt model that produced it;
- the applicable asset history row where relevant.

Power BI will use surrogate keys for relationships but will expose source identifiers in drill-through views for investigation.
