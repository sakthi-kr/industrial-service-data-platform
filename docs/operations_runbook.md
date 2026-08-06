# Operations runbook

## Purpose

This runbook covers routine checks, incident triage, recovery, and evidence collection for the
industrial service data platform. It is written for a small portfolio deployment but follows the
same separation used by production data systems: source ingestion, warehouse transformation,
reporting, enrichment, access control, and cost monitoring.

## Routine checks

### Before a demonstration or data refresh

1. Activate the local Python environment.
2. Run the deterministic recovery drills.
3. Run the live platform health command.
4. Confirm the health report is `PASS`.
5. Open Snowflake only when a live query or rebuild is needed.
6. Confirm the warehouse returns to auto-suspend after the work finishes.

Commands:

    source .venv/Scripts/activate
    python scripts/run_recovery_drills.py
    python scripts/check_platform_health.py

The live health command checks:

- latest ingestion status and age;
- received and rejected row counts;
- row counts for thirteen raw tables and four analytics marts;
- unresolved data-quality failures;
- invalid technician-note enrichment outputs;
- warehouse size, auto-suspend, and auto-resume.

## Severity levels

### Fail

A failed ingestion, stale source load, row-count drift, invalid structured output, failed quality
check, or warehouse cost-control change blocks publication and demonstrations.

### Warning

Warnings are reserved for conditions that need review but do not invalidate data. The current
health evaluator uses a strict pass/fail gate so unexpected states are not silently accepted.

## Incident triage order

1. Read the failed check name and remediation in `operational_health.json`.
2. Confirm whether the failure is local, ingestion-related, dbt-related, or Snowflake-related.
3. Preserve the failed run ID and query ID before changing anything.
4. Correct the narrowest failing layer.
5. Rerun only the failed component first.
6. Run the complete health check after recovery.
7. Record the result in the verification document.

## Common incidents

### Latest ingestion failed

Inspect `OPERATIONS.PIPELINE_RUNS`, then the matching `INGESTION_RESULTS` and
`REJECTED_RECORDS`. Correct the source or connection issue and rerun ingestion. Record hashes make
reruns duplicate-safe.

### Row count drift

Compare the affected raw table with its source CSV. For a mart, rebuild its upstream dbt chain using
`python scripts/run_dbt.py build --select +MODEL_NAME --fail-fast`.

### dbt build failure

Fix the first reported model or test. Use a targeted build before running the complete warehouse
build. Do not bypass tests or lower thresholds to force a pass.

### Enrichment output invalid

Regenerate predictions, validate the output contract locally, republish with the same model version,
and rebuild `MART_TECHNICIAN_NOTE_ENRICHMENT`.

### Power BI values stale

Run the live health check, rebuild dbt if needed, then refresh the imported Power BI model. Do not
change DAX measures to compensate for warehouse inconsistencies.

## Evidence retention

Keep private screenshots and detailed Snowflake results under
`C:\Users\admin\Downloads\Seimens`. Commit only sanitized JSON summaries and public documentation.
