# Analytics verification record

Complete this checklist only after rebuilding the live Snowflake analytics layer and running the
independent Python reconciliation.

- [x] `MART_KPI_SUMMARY` contains exactly one row.
- [x] The warehouse reporting timestamp matches the configured UTC timestamp.
- [x] Open case count matches the Python reference.
- [x] Critical open case count matches the Python reference.
- [x] Response SLA compliance matches within tolerance.
- [x] Resolution SLA compliance matches within tolerance.
- [x] Mean and median resolution hours match within one second.
- [x] First-time-fix rate matches within tolerance.
- [x] Repeat failure rate matches within tolerance.
- [x] Non-overlapping downtime matches within one second.
- [x] Delayed-part average and total service cost match their tolerances.
- [x] Alert-to-case conversion matches within tolerance.

Keep account identifiers, usernames, emails, and credentials out of public screenshots.

## Deployment result

Verified against the live Snowflake analytics layer. The independent Python reference calculations matched the warehouse KPI summary within the documented tolerances.
