
# dbt model design

## Purpose

The dbt project turns source-preserving raw tables into typed staging views, reusable warehouse
models, and reporting marts. The raw layer remains unchanged so every analytical value can be
traced back to the ingested source record.

## Layers

| Layer | Materialization | Responsibility |
|---|---|---|
| `STAGING` | Views | Type casting, text normalisation, and latest-record selection |
| `CORE` | Tables and one snapshot | Reusable dimensions, facts, keys, and business calculations |
| `ANALYTICS` | Tables | Power BI-ready service, asset, and customer datasets |

Thirteen staging views correspond one-to-one with the thirteen raw source tables. They use
`TRY_TO_*` conversions so invalid source text does not become an unhandled SQL conversion error.
The Python ingestion pipeline has already rejected invalid records; dbt tests provide an independent
warehouse-side check.

## Historical asset handling

`snap_asset_history` uses dbt's timestamp snapshot strategy with `asset_id` as the unique key and
`updated_at` as the change timestamp. The current dimensional row has a null `dbt_valid_to`; earlier
versions remain available after a changed asset source record is ingested and the snapshot runs
again.

## Core model grain

- `dim_customer`: one row per customer
- `dim_site`: one row per site
- `dim_asset`: one row per asset version
- `dim_service_contract`: one row per contract
- `dim_technician`: one row per technician
- `dim_part`: one row per part
- `fact_service_case`: one row per customer case
- `fact_service_order`: one row per service order
- `fact_service_order_part`: one row per service-order part line
- `fact_service_cost`: one row per service-cost transaction
- `fact_equipment_alert`: one row per monitoring alert
- `fact_technician_note`: one row per technician note

## Reporting marts

`mart_service_operations` provides monthly case, SLA, downtime, and cost measures by region,
priority, and fault category.

`mart_asset_reliability` provides one row per current asset with cases, service orders, alerts,
downtime, cost, and a transparent high-risk flag.

`mart_customer_performance` provides one row per customer with active assets, cases, SLA
performance, downtime, and service cost.

## Data-quality controls

The project includes generic tests for uniqueness, required fields, accepted values, relationships,
and expected row counts. Singular tests cover timestamp ordering, non-negative financial values,
completed-order completeness, composite-key uniqueness, and non-negative mart metrics.
