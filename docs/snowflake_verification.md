# Snowflake verification record

Use this page to record the result of the real Snowflake deployment. Do not mark an item complete from local static checks alone.

## Infrastructure

- [x] Database `INDUSTRIAL_SERVICE_DB` exists.
- [x] Warehouse `INDUSTRIAL_SERVICE_WH` is X-Small.
- [x] Automatic suspension is 60 seconds.
- [x] Automatic resume is enabled.
- [x] Resource monitor `INDUSTRIAL_SERVICE_MONITOR` is attached.
- [x] Schemas `RAW`, `STAGING`, `CORE`, `ANALYTICS`, and `OPERATIONS` exist.
- [x] Four operations tables exist.

## Roles and grants

- [x] `ISP_LOADER` can write to `RAW` and read ingestion audit tables.
- [x] `ISP_TRANSFORMER` can read `RAW` and write transformation schemas.
- [x] `ISP_ANALYST` can read `ANALYTICS`.
- [x] Loader access to `ANALYTICS` is denied.
- [x] Transformer writes to `RAW` are denied.
- [x] Analyst writes to `ANALYTICS` are denied.
- [x] Analyst access to `RAW` is denied.

## Evidence to retain

Save screenshots showing:

- the warehouse settings;
- the database schemas;
- the custom role hierarchy;
- the four operations tables;
- one successful check for each role;
- at least two expected access denials.

Do not include account locators, usernames, email addresses, or credentials in public screenshots.

## Deployment result

Verified in a live Snowflake account using Snowsight on 2026-08-04. The infrastructure checks,
functional-role access checks, and expected access-denial tests completed successfully.
