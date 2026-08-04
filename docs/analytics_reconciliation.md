# Analytics metric reconciliation

## Purpose

The warehouse metrics are checked against an independent Python implementation that reads the
same generated source files. The Python code does not query dbt models or reuse warehouse SQL. This
separation is deliberate: agreement between two independently implemented paths provides stronger
evidence than testing one SQL expression with another copy of the same expression.

## Reconciled metrics

The comparison covers twelve operational KPIs:

- open case count;
- critical open case count;
- response SLA compliance rate;
- resolution SLA compliance rate;
- mean resolution time;
- median resolution time;
- first-time-fix rate;
- repeat failure rate;
- non-overlapping equipment downtime;
- average delay among delayed part lines;
- total service cost;
- alert-to-case conversion rate.

Definitions and eligibility rules are maintained in `docs/kpi_catalogue.md`.

## Warehouse implementation

The dbt project adds three reusable intermediate models:

- `int_case_first_time_fix` evaluates the first completed visit and the following 30-day window;
- `int_case_repeat_failure` finds a later technical fault for the same asset and fault category;
- `int_asset_downtime` merges overlapping downtime intervals before aggregation.

`mart_kpi_summary` produces one row for the fixed `reporting_as_of` timestamp configured in
`dbt/dbt_project.yml`.

## Independent Python implementation

`src/industrial_service_platform/analytics/reference_metrics.py` reads five generated CSV files:

- `customer_cases.csv`;
- `service_orders.csv`;
- `service_order_parts.csv`;
- `service_costs.csv`;
- `equipment_alerts.csv`.

The implementation uses only Python's standard library. It handles nullable timestamps, fixed UTC
reporting time, 30-day observation windows, overlap-safe downtime, delayed-part eligibility, and
null denominators.

## Tolerances

Counts must match exactly. Rates must agree within `0.000001`. Durations may differ by at most one
second because Snowflake and Python expose floating-point values differently. Service cost must
match within one cent.

The tracked tolerances are in `config/analytics_reconciliation.json`.

## Running the comparison

Generate the source files and rebuild dbt before reconciliation:

    python -m industrial_service_platform generate-data
    python scripts/calculate_reference_metrics.py
    python scripts/run_dbt.py build --fail-fast
    python scripts/reconcile_analytics.py

The command prints the comparison and writes an ignored local report to:

    data/generated/analytics_reconciliation.json

A successful run exits with code zero and reports `all_metrics_passed` as `true`.

## Troubleshooting

A count mismatch usually indicates different eligibility rules or reporting timestamps. A duration
mismatch larger than one second usually indicates that overlapping downtime intervals were summed
without merging, or that part-delay averages included early deliveries. A first-time-fix or repeat
failure mismatch should be investigated by comparing the eligible case populations in
`sql/analytics/01_verify_kpi_populations.sql`.
