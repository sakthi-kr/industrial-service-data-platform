# Security and cost controls

## Access model

The platform uses separate Snowflake roles:

- `ISP_LOADER` writes validated records to `RAW` and audit tables;
- `ISP_TRANSFORMER` reads raw data and builds warehouse models;
- `ISP_ANALYST` reads approved analytics objects only;
- `ISP_ADMIN` inherits project roles and monitors the project warehouse.

Application scripts use the narrowest suitable role. `ACCOUNTADMIN`, `SECURITYADMIN`, and
`SYSADMIN` are reserved for explicit administrative work in Snowsight.

## Secret handling

Credentials are stored in ignored local files. GitHub workflows use placeholder values only for
credential-free dbt parsing. Screenshots must remove usernames, account identifiers, email
addresses, browser profiles, and personal bookmarks.

## GitHub security controls

- Dependabot checks Python and GitHub Actions dependencies monthly.
- Dependency review rejects new high-severity vulnerable dependencies in pull requests.
- CodeQL scans Python on pushes, pull requests, manual runs, and a weekly schedule.
- CI uses read-only repository permissions, explicit Python versions, timeouts, and dependency
  consistency checks.

## Snowflake cost controls

The project warehouse remains X-Small with 60-second auto-suspend and auto-resume. A resource
monitor limits monthly warehouse credits. Operational SQL reviews warehouse metering and failed
queries over a bounded seven-day window.

Snowflake Account Usage views can have latency. They are suitable for operational review, not for
sub-second alerting. The resource monitor applies to warehouse credit usage and does not cover every
serverless or AI-related Snowflake service.
