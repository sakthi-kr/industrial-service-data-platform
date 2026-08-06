# Technician-note enrichment setup

## Local prerequisites

Use the project virtual environment and install the updated dependencies:

    python -m pip install -e ".[dev]"

Generate the full source data before training:

    python -m industrial_service_platform generate-data

## Build the labelled dataset

    python scripts/build_note_enrichment_dataset.py

The generated file is written to
`data/generated/note_enrichment/labeled_notes.csv` and remains outside Git.

## Train and evaluate

    python scripts/train_note_enrichment.py

The command performs a service-order-grouped train/test split, evaluates a holdout model, evaluates
the masked-label challenge, retrains on all 5,000 notes, and writes:

- `data/generated/note_enrichment/model.joblib`;
- `data/generated/note_enrichment/evaluation.json`;
- `data/generated/note_enrichment/predictions.csv`;
- tracked sample evaluation and prediction files under `data/samples/note_enrichment/`.

The command returns a nonzero exit code if any required evaluation threshold fails.

## Publish to Snowflake

The existing `.env` connection is reused. The publisher overrides only the session role, database,
schema, and query tag. It never prints credentials.

    python scripts/publish_note_enrichment.py

A successful result should show:

    {
      "input_rows": 5000,
      "stored_rows": 5000,
      "status": "COMPLETED"
    }

Run the command a second time. `stored_rows` must remain 5,000 because the merge key is note ID plus
model version.

## Build the dbt mart

Parse before executing SQL:

    python scripts/run_dbt.py parse --no-partial-parse

Build the new mart and its upstream models:

    python scripts/run_dbt.py build --select +mart_technician_note_enrichment --fail-fast

The final summary must show `ERROR=0` and `SKIP=0`.

## Snowsight verification

Open **Projects → Workspaces** in Snowsight. Upload or paste each file under
`sql/note_enrichment/` and use **Run All**:

1. `00_verify_published_results.sql` checks the staging table, row count, model version, and mart.
2. `01_verify_enrichment_quality.sql` checks invalid rows, confidence bounds, and class counts.
3. `02_verify_analyst_access.sql` proves that `ISP_ANALYST` can read the analytics mart.

Do not put usernames, account identifiers, organisation names, or credentials in screenshots.
