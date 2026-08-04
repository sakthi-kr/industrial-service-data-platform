# Snowflake setup

## Prerequisites

Use a Snowflake account in which your user can activate `ACCOUNTADMIN`, `SECURITYADMIN`, and `SYSADMIN`. A trial account is sufficient for this project.

The setup uses an X-Small standard warehouse with automatic suspension after 60 seconds of inactivity, automatic resume, and a five-credit monthly resource monitor. The warehouse is created in a suspended state.

## Run order

Open a Snowsight SQL worksheet and run these files in order:

1. `sql/setup/00_create_roles.sql`
2. `sql/setup/01_create_database_warehouse.sql`
3. `sql/setup/02_create_resource_monitor.sql`
4. `sql/setup/03_create_schemas.sql`
5. `sql/setup/04_grant_access.sql`
6. `sql/setup/05_create_operations_tables.sql`
7. `sql/setup/06_verify_configuration.sql`

Run a complete file at a time. Stop if Snowflake returns an error; do not continue with the later files until the failed statement is understood and corrected.

## Grant the project roles to your user

The role hierarchy gives `SYSADMIN` oversight, but `USE ROLE` requires the selected custom role to be granted to the current user. Replace `YOUR_SNOWFLAKE_USER` with the unquoted user name shown by `SELECT CURRENT_USER();` and run:

    USE ROLE SECURITYADMIN;
    GRANT ROLE ISP_ADMIN TO USER YOUR_SNOWFLAKE_USER;
    GRANT ROLE ISP_LOADER TO USER YOUR_SNOWFLAKE_USER;
    GRANT ROLE ISP_TRANSFORMER TO USER YOUR_SNOWFLAKE_USER;
    GRANT ROLE ISP_ANALYST TO USER YOUR_SNOWFLAKE_USER;

Direct grants are used here only so the same user can switch among the four roles during portfolio verification. In a real team, each role would be granted only to the users or service accounts that need it.

## Verify access boundaries

After the setup files pass, run the files under `sql/verification/` in numeric order. The positive checks should succeed. Run each statement in `04_expected_denials.sql` separately and confirm that Snowflake rejects it.

Always run `99_cleanup_access_checks.sql` at the end, including after a failed verification attempt.

## Cost control

The resource monitor applies only to warehouse credit usage. It does not govern serverless or AI-service consumption. The warehouse should normally remain suspended when no query is running.

To inspect the warehouse later:

    SHOW WAREHOUSES LIKE 'INDUSTRIAL_SERVICE_WH';

The result should show an X-Small warehouse, `auto_suspend` equal to 60, and automatic resume enabled.
