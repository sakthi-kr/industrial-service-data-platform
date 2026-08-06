# Recovery procedures

## Recovery principles

- Recover the smallest failing layer first.
- Preserve run IDs, query IDs, and error messages before retrying.
- Prefer idempotent reruns over manual row editing.
- Never use `ACCOUNTADMIN` for application scripts.
- Do not delete audit or rejected-record history to make checks pass.

## Failed or interrupted ingestion

1. Query the latest row in `OPERATIONS.PIPELINE_RUNS`.
2. Query all matching rows in `OPERATIONS.INGESTION_RESULTS`.
3. Inspect `OPERATIONS.REJECTED_RECORDS` for source validation failures.
4. Fix the source file or connection problem.
5. Run local preparation before reconnecting:

       python -m industrial_service_platform prepare-ingestion

6. Rerun ingestion:

       python -m industrial_service_platform ingest

7. Confirm the latest run is `COMPLETED` and raw counts are unchanged or restored.

The raw loader uses deterministic record hashes and Snowflake `MERGE`, so replaying the same source
files does not duplicate accepted records.

## Failed dbt model or test

1. Stop at the first error.
2. Compile or parse the project after editing.
3. Run a targeted build:

       python scripts/run_dbt.py build --select +MODEL_NAME --fail-fast

4. Run the full build only after the targeted dependency chain passes.
5. Confirm the health report returns to `PASS`.

## Failed enrichment publication

1. Confirm local evaluation thresholds still pass.
2. Validate `predictions.csv` before connecting.
3. Republish using the same model version.
4. Confirm the staging table remains at 5,000 rows.
5. Rebuild the enrichment mart and rerun quality checks.

## Rollback drill

`sql/operations/05_transaction_rollback_drill.sql` creates a temporary table, inserts one row inside
an explicit transaction, rolls back, and verifies that zero rows remain. It does not touch project
business tables.

## Credential exposure

1. Revoke or rotate the exposed credential immediately.
2. Remove it from local files and Git history if it was committed.
3. Review GitHub secret-scanning and CodeQL results.
4. Confirm `.env` and `dbt/profiles.yml` remain ignored.
5. Record the incident privately without publishing the secret.

## Cost anomaly

1. Suspend the warehouse if unexpected usage is active.
2. Review `WAREHOUSE_METERING_HISTORY` and `QUERY_HISTORY`.
3. Identify the query tag, role, and time window responsible.
4. Restore X-Small sizing and 60-second auto-suspend.
5. Confirm the resource monitor remains attached.
