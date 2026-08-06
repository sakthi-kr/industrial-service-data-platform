# Power BI verification record

Complete this checklist only after building and checking the report.

- [x] The report uses Import mode with the Snowflake `ISP_ANALYST` role.
- [x] Only the four documented analytics marts are loaded.
- [x] The customer-to-asset relationship is active and single-direction.
- [x] No unintended relationship remains in Model view.
- [x] The supplied JSON theme is applied.
- [x] Every DAX measure in `dax_measures.dax` is created.
- [x] The Service Operations page contains all four slicers.
- [x] The Service Operations page contains all six KPI cards.
- [x] The Service Operations page contains the four specified analytical visuals.
- [x] The Asset and Customer page contains all five slicers.
- [x] The Asset and Customer page contains all five KPI cards.
- [x] The Asset and Customer page contains the four specified analytical visuals.
- [x] Power BI totals agree with the Snowflake verification queries.
- [x] Both sanitized page screenshots exist in the tracked dashboard directory.
- [x] The sanitized PDF export exists in the tracked dashboard directory.

Keep Snowflake account identifiers, usernames, emails, browser information, and credentials out of
tracked screenshots and exports.

## Deployment result

The Power BI report was connected to the Snowflake analytics layer, checked against the warehouse verification queries, and exported as sanitized screenshots and PDF evidence.
