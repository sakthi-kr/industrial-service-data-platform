# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses semantic versioning.

## [1.0.0] - 2026-08-06

### Added

- deterministic generation and validation for 13 linked industrial-service source datasets;
- Snowflake database, warehouse, managed-access schemas, resource monitor and functional roles;
- duplicate-safe Python ingestion with audit records and rejected-record handling;
- dbt staging, dimensional, fact, snapshot and analytics models with data tests;
- independent Python reconciliation for 12 service and reliability KPIs;
- two-page Power BI report with documented DAX, model relationships, screenshots and PDF export;
- evaluated technician-note classification, triage, component routing and grounded summaries;
- Snowflake publication and dbt modelling for 5,000 enrichment records;
- operational health checks, deterministic recovery drills, rollback verification and runbooks;
- Python 3.10–3.12 CI, CodeQL, Dependabot and pull-request dependency review;
- final architecture, reproducibility, portfolio and release documentation.

### Security

- credentials, local profiles, generated datasets, private screenshots and Power BI working files are excluded from version control;
- least-privilege Snowflake access and bounded warehouse-cost controls are documented and live-verified.
