# Industrial Service Data & AI Platform

This project models day-to-day service operations for industrial equipment. It brings together customer cases, assets, work orders, spare parts, equipment alerts, and technician notes so the data can be checked, transformed, and used for reporting.

The project uses synthetic data. It is not intended to reproduce a full ERP or CRM system. The aim is to build a complete and testable workflow from source data to an analytics layer, with enough operational detail to make the results useful rather than purely illustrative.

## Project status

Phases 0, 1, and 2 are complete. The repository now includes the development setup, documented
business and data model, deterministic synthetic source datasets, schema and relationship checks,
controlled invalid examples, tracked samples, and reproducibility manifests.

The next phase will create the Snowflake database, schemas, warehouse, roles, and grants. dbt,
Power BI, and technician-note enrichment will be added after the ingestion and warehouse layers are
working.

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
are kept in `data/samples/phase2/`.

    python -m industrial_service_platform generate-data
    python -m industrial_service_platform validate-data

The generator uses a fixed seed and reporting timestamp. Repeated runs with the same configuration
produce the same file content and SHA-256 hashes.

## Project phases

0. Repository and development environment
1. Business scenario and data model
2. Synthetic industrial datasets
3. Snowflake infrastructure
4. Python ingestion pipeline
5. dbt transformations and data quality
6. Analytics metrics and SQL validation
7. Power BI dashboard
8. Technician-note enrichment
9. Operations, reliability, security, and CI
10. Final documentation and GitHub release

## Data and credentials

Only generated data and optional public sandbox data will be used. Real customer data, credentials, Snowflake keys, local dbt profiles, generated datasets, and Power BI working files are excluded from version control.

## Licence

This project is released under the MIT License.
