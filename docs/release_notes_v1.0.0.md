# Industrial Service Data & AI Platform v1.0.0

This release is the first complete portfolio version of the industrial service data and AI platform.

## Highlights

- 13 deterministic operational datasets and 107,724 generated records;
- live-verified Snowflake infrastructure and least-privilege access;
- validated, audited and duplicate-safe Python ingestion;
- tested dbt transformations, snapshot history and analytics marts;
- independent reconciliation of 12 KPIs;
- two-page Power BI report with documented model and DAX;
- evaluated enrichment and Snowflake publication for 5,000 technician notes;
- operational health checks, recovery drills, cost review and security workflows;
- Python 3.10–3.12 CI, CodeQL, Dependabot and dependency review.

## Release assets

- `industrial-service-dashboard-v1.0.0.pbix` — interactive Power BI report;
- `industrial-service-dashboard-v1.0.0.pdf` — reviewable two-page export;
- `industrial-service-platform-evidence-v1.0.0.zip` — dashboard screenshots and sanitized evaluation/operations evidence;
- `SHA256SUMS.txt` — checksums for the uploaded assets.

## Reproduction

Follow `docs/reproducibility.md`. Snowflake credentials and external software are required for the live warehouse and Power BI portions. The repository contains no real customer data.

## Known limitations

The dataset and technician notes are synthetic. The text model relies strongly on direct fault terminology, and the masked-label challenge reports this explicitly. SLA calculations use elapsed hours, and continuous hosted monitoring is outside scope.
