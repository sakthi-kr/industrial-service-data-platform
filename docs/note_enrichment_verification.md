# Technician-note enrichment verification

Tick an item only after observing the result locally or in Snowflake.

- [x] The updated development dependencies install successfully.
- [x] The generated source directory contains 5,000 technician notes.
- [x] The labelled dataset contains 5,000 rows.
- [x] Training and test service-order groups do not overlap.
- [x] Fault-category macro F1 meets the configured threshold.
- [x] Priority macro F1 meets the configured threshold.
- [x] Component exact-match accuracy meets the configured threshold.
- [x] Structured-output validity is 100 percent.
- [x] The masked-label challenge is recorded in the public evaluation summary.
- [x] The final model artifact and 5,000 predictions are generated locally.
- [x] Snowflake publication stores 5,000 rows for the model version.
- [x] Repeating Snowflake publication does not increase the stored row count.
- [x] The dbt enrichment mart builds with no errors or skipped nodes.
- [x] The enrichment mart contains 5,000 unique note IDs.
- [x] Invalid-output and confidence-bound checks both return zero.
- [x] `ISP_ANALYST` can query the enrichment mart.
- [x] The complete local test and CI gates pass.

Keep private screenshots of the evaluation summary, first publication, repeated publication, dbt
build, Snowflake quality checks, and analyst query. Crop all account and identity information.

## Deployment result

Verified locally and against Snowflake on 2026-08-06. The grouped holdout evaluation, lexical-ablation challenge, structured-output checks, idempotent publication, dbt mart, and analyst-role queries completed successfully.
