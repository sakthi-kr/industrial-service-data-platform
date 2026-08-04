# Ingestion verification record

Complete this checklist only after running the pipeline against the live Snowflake account.

## Local checks

- [x] The Snowflake connector installs in the project virtual environment.
- [x] `test-snowflake` reports `ISP_LOADER`, the project warehouse, database, and raw schema.
- [x] Source preparation reports all expected rows and no rejected rows for the generated dataset.
- [x] The complete automated test suite passes.

## First load

- [x] Thirteen raw tables exist.
- [x] The full ingestion command completes successfully.
- [x] Raw table counts match the generated source counts.
- [x] One pipeline-run record is marked completed.
- [x] Thirteen dataset result records exist for the run.
- [x] No generated valid source rows appear in `REJECTED_RECORDS`.

## Idempotent rerun

- [x] Running the same command again completes successfully.
- [x] The second run loads zero new raw rows.
- [x] Raw table counts remain unchanged.
- [x] Dataset results record skipped rows through the difference between received and loaded counts.

## Evidence

Keep private screenshots of the connection result, raw table list, row-count query, latest pipeline
runs, and the idempotent rerun comparison. Crop usernames, account identifiers, organisation names,
and browser-profile information before publishing any screenshot.

## Deployment result

Verified against a live Snowflake account using Snowsight on 2026-08-04. The initial load, audit records, raw row counts, and duplicate-safe rerun completed successfully.
