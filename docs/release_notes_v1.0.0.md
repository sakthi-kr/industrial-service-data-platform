# Industrial Service Data & AI Platform v1.0.0

`v1.0.0` is the first audited portfolio version of the industrial service data and AI platform. It is published as an annotated Git tag rather than a GitHub Release.

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

## Public artefacts

The repository includes:

- dashboard screenshots under `dashboards/power_bi/screenshots/`;
- the reviewable PDF at `dashboards/power_bi/exports/industrial_service_dashboard.pdf`;
- sanitized evaluation and operational summaries under `data/samples/`;
- architecture, reproducibility and verification documentation under `docs/`.

The editable Power BI `.pbix` file remains local and is not distributed through GitHub.

## Reproduction

Follow `docs/reproducibility.md`. Snowflake credentials and Power BI Desktop are required for the live warehouse and report-building portions. The repository contains no real customer data.

## Known limitations

The datasets and technician notes are synthetic. The text model relies strongly on direct fault terminology, which the masked-label challenge reports explicitly. SLA calculations use elapsed hours, and continuous hosted monitoring is outside scope.
