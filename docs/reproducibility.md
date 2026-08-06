# Reproducibility guide

## Preconditions

- Windows with Git Bash, Python 3.10 and Power BI Desktop;
- a Snowflake account whose user can receive the project roles;
- `.env` created from `.env.example`;
- `dbt/profiles.yml` created from `dbt/profiles.example.yml`.

Do not place passwords, account identifiers, local profiles or private screenshots in the repository.

## 1. Install

```bash
py -3.10 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
pre-commit install
```

## 2. Generate and validate source data

```bash
python -m industrial_service_platform generate-data
python -m industrial_service_platform validate-data
python -m industrial_service_platform prepare-ingestion
```

Expected source total: 107,724 accepted records across 13 datasets.

## 3. Create Snowflake infrastructure

Run the SQL files under `sql/setup/` in numeric order in Snowsight. Grant the four project roles to the portfolio user, then run the access-verification SQL under `sql/verification/`.

## 4. Ingest

```bash
python -m industrial_service_platform test-snowflake
python -m industrial_service_platform create-raw-tables
python -m industrial_service_platform ingest
python -m industrial_service_platform ingest
```

The first run loads the records. The second receives the same records but loads zero new rows.

## 5. Build dbt models

```bash
python scripts/run_dbt.py debug
python scripts/run_dbt.py parse --no-partial-parse
python scripts/run_dbt.py build --fail-fast
python scripts/run_dbt.py docs generate
```

Require `ERROR=0` and `SKIP=0`.

## 6. Reconcile KPIs

```bash
python scripts/calculate_reference_metrics.py
python scripts/reconcile_analytics.py
```

Require `all_metrics_passed: true` for all 12 configured metrics.

## 7. Train and publish note enrichment

```bash
python scripts/build_note_enrichment_dataset.py
python scripts/train_note_enrichment.py
python scripts/publish_note_enrichment.py
python scripts/publish_note_enrichment.py
python scripts/run_dbt.py build --select +mart_technician_note_enrichment --fail-fast
```

Require grouped train/test isolation, all evaluation thresholds, 5,000 valid prediction rows, and 5,000 stored rows after both publications.

## 8. Review Power BI

Follow `docs/power_bi_setup.md`. Load only the four documented analytics marts, create the specified relationship and measures, verify benchmark values, and export the two-page report to PDF.

## 9. Operational verification

```bash
python scripts/run_recovery_drills.py
python scripts/check_platform_health.py
```

Run the SQL under `sql/operations/` to verify monitoring views, row counts, warehouse settings, historical failures and transaction rollback.

## 10. Full repository gate

```bash
python -m pip check
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m pytest
python scripts/validate_snowflake_setup.py
python scripts/validate_dbt_project.py
python scripts/validate_analytics_assets.py
python scripts/validate_power_bi_assets.py
python scripts/validate_note_enrichment_assets.py
python scripts/run_recovery_drills.py
python scripts/validate_operational_assets.py
python scripts/validate_release_assets.py
pre-commit run --all-files
git diff --check
```

The exact pytest count can increase when regression tests are added; the gate is that every collected test passes.
