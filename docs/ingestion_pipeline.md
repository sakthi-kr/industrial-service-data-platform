# Python ingestion pipeline

## Purpose

The ingestion pipeline moves generated ERP-, CRM-, monitoring-, and field-service CSV files into the
Snowflake `RAW` schema. It validates the complete source set before opening a Snowflake connection,
keeps rejected rows out of business tables, records each run in `OPERATIONS`, and avoids inserting
the same source record twice.

## Processing flow

    Discover all configured CSV files
                    |
          Read and validate rows
                    |
       Repeat reference checks after
            invalid parent rows drop
                    |
         Accepted / rejected split
                    |
       Create raw tables when missing
                    |
      Load accepted rows to a temporary
          Snowflake table in batches
                    |
       Merge records not already present
          by deterministic SHA-256 hash
                    |
       Record dataset and run audit data

## Source validation

The pipeline uses `config/source_schema.json` as the contract for all thirteen datasets. Validation
covers:

- required files and columns;
- required and nullable fields;
- allowed category values;
- dates, timestamps, numbers, and booleans;
- duplicate business keys;
- foreign-key references;
- source-specific timestamp and financial rules.

Validation runs before Snowflake is contacted. If a parent row is rejected, the remaining accepted
set is checked again so dependent child rows cannot be loaded with unresolved references.

## Raw table design

Each raw table keeps source fields as `VARCHAR`. Type casting and business transformations belong in
the later staging layer. Six technical columns are added to every raw table:

| Column | Purpose |
|---|---|
| `_LOAD_BATCH_ID` | Identifies one dataset load attempt |
| `_SOURCE_SYSTEM` | ERP, CRM, monitoring, or field service |
| `_SOURCE_FILE_NAME` | Original CSV filename |
| `_SOURCE_ROW_NUMBER` | Original CSV row number including the header offset |
| `_INGESTED_AT` | UTC timestamp when the record was loaded |
| `_RECORD_HASH` | Deterministic SHA-256 hash of the source fields |

## Idempotency

Accepted rows are first inserted into a temporary Snowflake table. A `MERGE` adds only records whose
`_RECORD_HASH` does not already exist in the target raw table. Re-running the same source files
therefore loads zero new rows and reports the existing rows as skipped.

Idempotency is based on complete source-record content. A changed source row receives a different
hash and is retained as a new raw ingestion event. The later staging layer will decide which source
version is current.

## Rejected records

A rejected source row is not written to a raw business table. Each validation issue is recorded in
`OPERATIONS.REJECTED_RECORDS` with the source file, original row number, business identifier,
validation code, message, and original row payload.

The run summary counts distinct rejected source rows. The rejection table can contain more records
than that count because one row can fail several checks.

## Audit records

`OPERATIONS.PIPELINE_RUNS` stores one row for the complete command. `OPERATIONS.INGESTION_RESULTS`
stores one row per dataset. Successful, failed, repeated, and partially rejected executions remain
visible without relying on terminal logs.

## Failure handling

Connection attempts are retried using the values in `config/ingestion.json`. Dataset writes use an
explicit transaction. If a load fails, its temporary inserts, raw merge, rejection records, and
dataset result are rolled back together. The run is marked failed when the connection remains
usable. Because the raw merge is idempotent, the command can be run again after the underlying issue
is corrected.

## Security

Credentials are read from the ignored `.env` file or process environment. A standard trial account can
use Snowflake username-and-password authentication. Accounts with browser-based SSO can instead use
`externalbrowser`. The connection uses `ISP_LOADER`, whose permissions are restricted to the warehouse,
`RAW`, and the required operations tables.
