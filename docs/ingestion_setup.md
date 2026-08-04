# Running the Snowflake ingestion pipeline

This guide assumes that the Snowflake database, warehouse, schemas, roles, grants, and operations
tables have already been created and verified.

## Install the connector

Activate the project environment and reinstall the editable package so the pinned Snowflake connector
is available:

    source .venv/Scripts/activate
    python -m pip install -e ".[dev]"

Confirm the installed connector version:

    python -c "import snowflake.connector; print(snowflake.connector.__version__)"

The project is tested with Snowflake Connector for Python 4.2.0.

## Find the connection values in Snowsight

Open a SQL workspace in Snowsight and run:

    SELECT
      CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME()
        AS ACCOUNT_IDENTIFIER,
      CURRENT_USER() AS USER_NAME;

Copy the two returned values privately. The account identifier must not include
`.snowflakecomputing.com`.

## Create the local environment file

In Git Bash, from the repository root:

    cp .env.example .env

Open `.env` in PyCharm or a text editor and set:

    SNOWFLAKE_ACCOUNT=your_org-your_account
    SNOWFLAKE_USER=your_user_name
    SNOWFLAKE_AUTHENTICATOR=snowflake
    SNOWFLAKE_PASSWORD=your_snowflake_password
    SNOWFLAKE_ROLE=ISP_LOADER
    SNOWFLAKE_WAREHOUSE=INDUSTRIAL_SERVICE_WH
    SNOWFLAKE_DATABASE=INDUSTRIAL_SERVICE_DB
    SNOWFLAKE_SCHEMA=RAW

The `.env` file is ignored by Git. Never paste its contents into an issue, screenshot, commit, or
chat message. If browser-based SSO is configured for the account, set the authenticator to
`externalbrowser` and leave the password empty. Do not use `externalbrowser` for a standard native
user unless SSO has been configured.

## Test the connection

Run:

    python -m industrial_service_platform test-snowflake

For password authentication, the command connects directly. For configured browser-based SSO, a browser
window opens for approval. A successful result contains only non-secret session context:

    {
      "connected": true,
      "database": "INDUSTRIAL_SERVICE_DB",
      "role": "ISP_LOADER",
      "schema": "RAW",
      "warehouse": "INDUSTRIAL_SERVICE_WH"
    }

If password authentication fails, verify the account identifier, user, and password in `.env`. If an SSO
browser does not open, copy the URL printed in the terminal into your browser. If Snowflake reports that
`ISP_LOADER` is unavailable, grant the role to your user again with `SECURITYADMIN`.

## Generate and prepare the source data

Generate the deterministic full datasets:

    python -m industrial_service_platform generate-data

Validate and split the files locally without contacting Snowflake:

    python -m industrial_service_platform prepare-ingestion

The expected full-data result is 107,724 received rows, 107,724 accepted rows, and zero rejected
rows. The local report is written under `data/generated/ingestion_reports/`, which is excluded from
Git.

## Create the raw tables

Run:

    python -m industrial_service_platform create-raw-tables

This creates or verifies thirteen tables in `INDUSTRIAL_SERVICE_DB.RAW`. It does not delete existing
rows.

For a quick first check, create and load only customers:

    python -m industrial_service_platform create-raw-tables --dataset customers
    python -m industrial_service_platform ingest --dataset customers

After the small check succeeds, load all datasets:

    python -m industrial_service_platform ingest

Keep the terminal open until the JSON run summary is printed. Do not stop the process while a dataset
is being loaded. The warehouse automatically suspends after inactivity.

## Prove that reruns are safe

Run the same command again:

    python -m industrial_service_platform ingest

The second run should report zero newly loaded rows and show the accepted rows as skipped. This proves
that the hash-based merge prevents duplicate raw records.

## Verify the result in Snowsight

Open and run `sql/ingestion/00_verify_ingestion.sql`. Confirm that:

- thirteen raw tables exist;
- raw row counts match the generated source counts;
- the latest pipeline run completed;
- every dataset has an ingestion result;
- the second identical run loaded zero new rows.

Use `sql/ingestion/01_verify_idempotency.sql` after the second run for a focused comparison.

## Common errors

### Account identifier is invalid

Use the exact value returned by:

    SELECT CURRENT_ORGANIZATION_NAME() || '-' || CURRENT_ACCOUNT_NAME();

Do not append `.snowflakecomputing.com`.

### Role does not exist or is not authorized

In Snowsight, use `SECURITYADMIN` and grant the loader role to your user:

    GRANT ROLE ISP_LOADER TO USER your_user_name;

### Warehouse is suspended

No manual action is normally required. The warehouse has auto-resume enabled. Confirm that `.env`
uses `INDUSTRIAL_SERVICE_WH`.

### Source files are missing

Run the generator again from the repository root:

    python -m industrial_service_platform generate-data

### The connection closes during a load

The run should be marked failed when possible. Correct the connection issue and rerun the command.
Previously merged records are skipped rather than duplicated.
