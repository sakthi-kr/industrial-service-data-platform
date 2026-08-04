
# dbt verification record

Complete this checklist only after running the project against the live Snowflake account.

## Local setup

- [x] dbt Core and the Snowflake adapter report version 1.12.0.
- [x] `dbt/profiles.yml` exists locally and remains ignored by Git.
- [x] `python scripts/run_dbt.py debug` succeeds with `ISP_TRANSFORMER`.
- [x] `python scripts/run_dbt.py parse --no-partial-parse` succeeds.

## Warehouse build

- [x] The full `dbt build` command completes without model or test failures.
- [x] Thirteen staging views exist in `STAGING`.
- [x] The asset snapshot exists in `CORE` with 1,000 current records.
- [x] Twelve core dimensions and facts exist in `CORE`.
- [x] Three reporting marts exist in `ANALYTICS`.
- [x] Staging and core row counts match the documented source counts.

## Data quality and documentation

- [x] All generic and singular data tests pass.
- [x] No negative cost, duration, quantity, or count violations are returned.
- [x] `dbt docs generate` completes successfully.
- [x] The lineage graph connects raw sources through staging and core models to all three marts.
- [x] The analyst role can query the analytical marts.

## Evidence

Keep private screenshots of the successful build summary, Snowflake object lists, test summary,
asset snapshot query, mart samples, and lineage graph. Crop account identifiers, usernames,
organisation names, email addresses, and browser-profile information.

## Deployment result

Verified against the live Snowflake account on 2026-08-04. The full build, data tests, asset snapshot, reporting marts, analyst access, and generated lineage documentation completed successfully.
