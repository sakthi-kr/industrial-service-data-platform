# Portfolio summary

## One-sentence description

Built an end-to-end industrial service data and AI platform using Python, Snowflake, dbt, SQL and Power BI, with duplicate-safe ingestion, tested analytics, independent KPI reconciliation, evaluated technician-note enrichment and operational controls.

## Evidence

- Generated 107,724 deterministic records across 13 linked ERP-, CRM-, monitoring- and field-service-style datasets.
- Designed Snowflake schemas, roles, grants, warehouse cost controls and operational audit tables.
- Implemented validated, transaction-aware and duplicate-safe Python ingestion.
- Built dbt staging, dimensional, fact, snapshot and analytics models with generic and singular tests.
- Reconciled 12 KPIs independently between Python and Snowflake using explicit tolerances.
- Built and validated a two-page Power BI report with 18 DAX measures.
- Trained and evaluated TF-IDF and logistic-regression classifiers, then published 5,000 structured note enrichments.
- Added platform health checks, recovery drills, CI across Python 3.10–3.12, CodeQL and dependency review.

## CV bullets

- Built a reproducible industrial-service analytics platform integrating Python ingestion, Snowflake, dbt and Power BI across 13 synthetic operational datasets and 107k+ records.
- Implemented schema validation, rejected-record handling, transaction rollback, audit logging and hash-based idempotency; verified duplicate-safe reloads in Snowflake.
- Developed tested dbt dimensions, facts, snapshots and marts, and independently reconciled 12 service KPIs between Python and Snowflake.
- Evaluated a grouped-split TF-IDF/logistic-regression pipeline for technician-note fault and priority classification and published 5,000 validated predictions.
- Added least-privilege roles, warehouse cost controls, health checks, recovery drills, multi-version CI, CodeQL and dependency review.

## Interview discussion points

### Why preserve raw values as text?

It prevents silent type coercion and retains traceability to the original export. dbt staging performs explicit conversion, so malformed values can be detected and tested.

### How is idempotency implemented?

A deterministic SHA-256 hash is calculated from the complete source row. Snowflake `MERGE` inserts only hashes that do not already exist while still recording each pipeline run.

### How are KPI errors detected?

Warehouse results are compared with an independent Python implementation that reads generated CSVs. Counts are exact; rates, durations and currency use documented tolerances.

### How was leakage controlled in text evaluation?

The split groups rows by service order so related notes cannot appear in both training and test data. A masked-label challenge also tests dependence on explicit fault words.

### What would change in production?

Use real source connectors and orchestration, environment-specific infrastructure as code, secret management, incremental models, business calendars, scheduled monitoring, model drift checks and Power BI Service deployment.
