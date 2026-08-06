"""Keep the public README aligned with the implemented repository."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")

STATUS = """## Project status
The repository includes a reproducible Python environment, a documented business and data model,
deterministic synthetic source datasets, live-verified Snowflake infrastructure, a validated
idempotent ingestion pipeline, tested dbt models, independent reconciliation of twelve service and
reliability KPIs, a documented two-page Power BI report, and evaluated technician-note enrichment.
Operational hardening and the final repository release are the remaining implementation areas.
"""

DBT = """## dbt transformations and data quality
The dbt project converts source-preserving raw tables into typed staging views, reusable dimensions
and facts, an asset-history snapshot, and reporting marts. Generic and singular tests check keys,
relationships, allowed values, expected row counts, timestamps, financial rules, and KPI bounds.
    cp dbt/profiles.example.yml dbt/profiles.yml
    python scripts/run_dbt.py debug
    python scripts/run_dbt.py parse --no-partial-parse
    python scripts/run_dbt.py build
    python scripts/run_dbt.py docs generate
Setup, model design, live verification, and troubleshooting are documented in `docs/dbt_setup.md`,
`docs/dbt_model_design.md`, and `docs/dbt_verification.md`.
"""

ANALYTICS = """## Analytics metric reconciliation
Twelve warehouse KPIs are compared with an independent Python implementation that reads the
generated source files. Counts must match exactly, while rates, durations, and cost use explicit
metric-specific tolerances.
    python -m industrial_service_platform generate-data
    python scripts/run_dbt.py build --fail-fast
    python scripts/reconcile_analytics.py
Definitions, tolerances, verification steps, and mismatch diagnosis are documented in
`docs/analytics_reconciliation.md` and `docs/analytics_verification.md`.
"""

POWER_BI = """## Power BI reporting
The Power BI report uses four tested analytics marts, a documented customer-to-asset relationship,
filter-safe DAX measures, a tracked JSON theme, and two report pages covering service operations and
asset/customer analysis. The binary `.pbix` file stays outside Git; sanitized screenshots and a PDF
export provide reviewable evidence.
    python scripts/validate_power_bi_assets.py
Connection steps, the report model, measures, visual specification, and verification process are
documented in `docs/power_bi_setup.md` and `dashboards/power_bi/`.
"""

ENRICHMENT = """## Technician-note enrichment
A reproducible sparse-text pipeline classifies fault category and triage priority from technician
notes and permitted operational context. Evaluation uses a service-order-grouped holdout split,
reports macro F1 and accuracy, and includes a masked-label challenge to expose dependence on direct
fault phrases. Components, service-team routing, and summaries are generated deterministically from
validated labels rather than an external language-model API.
    python -m industrial_service_platform generate-data
    python scripts/train_note_enrichment.py
    python scripts/publish_note_enrichment.py
    python scripts/run_dbt.py build --select mart_technician_note_enrichment --fail-fast
Design choices, limitations, Snowflake publication, and verification are documented in
`docs/note_enrichment_design.md`, `docs/note_enrichment_setup.md`, and
`docs/note_enrichment_verification.md`.
"""


def replace_section(text: str, heading: str, replacement: str) -> str:
    """Replace one second-level Markdown section using heading boundaries."""
    start = text.find(heading)
    if start == -1:
        raise RuntimeError(f"README section was not found: {heading}")
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[:start] + replacement.rstrip() + "\n"
    return text[:start] + replacement.rstrip() + "\n\n" + text[next_heading + 1 :]


def insert_before(text: str, marker: str, section: str) -> str:
    """Insert a section before a stable README heading."""
    if marker not in text:
        raise RuntimeError(f"README marker was not found: {marker}")
    return text.replace(marker, section.rstrip() + "\n\n" + marker, 1)


def main() -> int:
    """Update implementation status and public technical sections."""
    text = README_PATH.read_text(encoding="utf-8")
    text = replace_section(text, "## Project status", STATUS)
    text = replace_section(text, "## dbt transformations and data quality", DBT)
    if "## Analytics metric reconciliation" in text:
        text = replace_section(text, "## Analytics metric reconciliation", ANALYTICS)
    else:
        text = insert_before(text, "## Data and credentials", ANALYTICS)
    if "## Power BI reporting" in text:
        text = replace_section(text, "## Power BI reporting", POWER_BI)
    else:
        text = insert_before(text, "## Data and credentials", POWER_BI)
    if "## Technician-note enrichment" in text:
        text = replace_section(text, "## Technician-note enrichment", ENRICHMENT)
    else:
        text = insert_before(text, "## Data and credentials", ENRICHMENT)
    with README_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("README updated with evaluated technician-note enrichment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
