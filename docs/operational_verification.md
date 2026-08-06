# Operational verification

Complete each item only after observing the stated result.

- [x] Operational asset validation passes locally.
- [x] Monitoring views are created in the `OPERATIONS` schema.
- [x] Latest pipeline status is `COMPLETED`.
- [x] Latest pipeline run is within the configured freshness window.
- [x] Latest rejected-row rate is below the configured threshold.
- [x] All thirteen raw-table counts match the verified baseline.
- [x] All four monitored analytics-mart counts match the verified baseline.
- [x] No unresolved failed data-quality checks are recorded.
- [x] No invalid technician-note enrichment outputs are present.
- [x] Warehouse size is X-Small.
- [x] Warehouse auto-suspend is 60 seconds or less.
- [x] Warehouse auto-resume is enabled.
- [x] All deterministic recovery drills detect their injected failure.
- [x] Temporary-table transaction rollback leaves zero rows.
- [x] Seven-day warehouse credit usage has been reviewed.
- [x] Seven-day failed query history has been reviewed.
- [x] Dependabot version-update configuration is present.
- [x] Dependabot alerts and security updates are enabled in repository settings.
- [x] Dependency review workflow is present for pull requests.
- [x] CodeQL Python analysis completes successfully.

## Private evidence

Store screenshots outside the repository. Remove credentials, usernames, account identifiers,
organisation names, email addresses, personal browser information, and bookmarks before sharing.

## Deployment result

Verified on 2026-08-06 using local recovery drills, live Snowflake health checks, cost-control review, and GitHub security workflows.
