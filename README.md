# Industrial Service Data & AI Platform

This project models day-to-day service operations for industrial equipment. It brings together customer cases, assets, work orders, spare parts, equipment alerts, and technician notes so the data can be checked, transformed, and used for reporting.

The project uses synthetic data. It is not intended to reproduce a full ERP or CRM system. The aim is to build a complete and testable workflow from source data to an analytics layer, with enough operational detail to make the results useful rather than purely illustrative.

## Project status

The repository includes a reproducible Python environment, a documented business and data model,
deterministic synthetic source datasets, live-verified Snowflake infrastructure, a validated
idempotent ingestion pipeline, and tested dbt models across the staging, core, and analytics layers.
Power BI reporting and technician-note enrichment are the next implementation areas.

## Planned data flow

    ERP-style exports        CRM-style exports
             \                    /
              \                  /
               Python ingestion
                      |
              Snowflake raw layer
                      |
          dbt models and data tests
                      |
             Analytics data models
                 /          \
          Power BI      Note enrichment

## Planned scope

The finished project will include:

- synthetic data for customers, sites, assets, service cases, work orders, parts, alerts, and technician notes;
- Python ingestion with schema validation, batch tracking, duplicate protection, and rejected-record handling;
- Snowflake schemas for raw, staging, core, analytics, and operational data;
- dbt transformations, tests, snapshots, and generated documentation;
- SQL and Python checks to confirm that reported service metrics are calculated correctly;
- a Power BI report for service operations and asset-level analysis;
- a small evaluated enrichment step for classifying and summarising technician notes;
- automated tests, continuous integration, access-control scripts, and an operations runbook.

## Repository layout

- `config/` — project and data-generation configuration
- `dashboards/` — dashboard documentation, screenshots, and exports
- `data/` — local raw, generated, and sample data
- `dbt/` — dbt models, tests, snapshots, and project configuration
- `docs/` — architecture notes, data definitions, and runbooks
- `scripts/` — setup and data-generation scripts
- `sql/` — Snowflake setup and analysis SQL
- `src/industrial_service_platform/` — Python package
- `tests/` — automated tests

## Local development

The project currently targets Python 3.10.

    py -3.10 -m venv .venv
    source .venv/Scripts/activate
    python -m pip install --upgrade pip setuptools wheel
    python -m pip install -e ".[dev]"

Run the local checks with:

    python -m ruff check .
    python -m ruff format --check .
    python -m mypy src
    python -m pytest

Run all configured pre-commit checks with:

    pre-commit run --all-files

## Synthetic data generation

The default configuration generates the full ERP-, CRM-, monitoring-, and field-service-style
source files locally. Generated files are excluded from Git; small samples and validation metadata
are kept in `data/samples/source_data/`.

    python -m industrial_service_platform generate-data
    python -m industrial_service_platform validate-data

The generator uses a fixed seed and reporting timestamp. Repeated runs with the same configuration
produce the same file content and SHA-256 hashes.


## Snowflake infrastructure

The Snowflake setup creates an X-Small warehouse, a monthly resource monitor, five managed-access
schemas, four functional roles, future grants, and operations tables for ingestion and data-quality
audit records.

Setup and access checks are documented in `docs/snowflake_setup.md` and
`docs/snowflake_verification.md`. The verification record includes the completed live deployment and
least-privilege access checks.

## Python ingestion pipeline

The ingestion command validates all configured CSV files before connecting to Snowflake, separates
accepted and rejected rows, creates missing raw tables, and loads accepted records in batches. It
also writes run-level and dataset-level audit records. A deterministic record hash prevents
duplicate inserts when the same files are loaded again.

    python -m industrial_service_platform prepare-ingestion
    python -m industrial_service_platform test-snowflake
    python -m industrial_service_platform create-raw-tables
    python -m industrial_service_platform ingest

Connection setup, live verification, expected outputs, and common errors are documented in
`docs/ingestion_setup.md`.

## dbt transformations and data quality

The dbt project converts source-preserving raw tables into typed staging views, reusable dimensions
and facts, an asset-history snapshot, and three reporting marts. Generic and singular tests check
keys, relationships, allowed values, expected row counts, timestamps, and financial rules.

    cp dbt/profiles.example.yml dbt/profiles.yml
    python scripts/run_dbt.py debug
    python scripts/run_dbt.py parse --no-partial-parse
    python scripts/run_dbt.py build
    python scripts/run_dbt.py docs generate

Setup, model design, live verification, and troubleshooting are documented in `docs/dbt_setup.md`,
`docs/dbt_model_design.md`, and `docs/dbt_verification.md`.

## Data and credentials

Only generated data and optional public sandbox data will be used. Real customer data, credentials, Snowflake keys, local dbt profiles, generated datasets, and Power BI working files are excluded from version control.

## Licence

This project is released under the MIT License.
