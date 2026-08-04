"""Keep the public README aligned with the implemented repository."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")

STATUS = """## Project status
The repository includes a reproducible Python environment, a documented business and data model,
deterministic synthetic source datasets, live-verified Snowflake infrastructure, a validated
idempotent ingestion pipeline, tested dbt models, and independent reconciliation of twelve service
and reliability KPIs. Power BI reporting and technician-note enrichment are the next implementation
areas.
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
    """Update implementation status, dbt, and reconciliation sections."""
    text = README_PATH.read_text(encoding="utf-8")
    text = replace_section(text, "## Project status", STATUS)
    text = replace_section(text, "## dbt transformations and data quality", DBT)
    if "## Analytics metric reconciliation" in text:
        text = replace_section(text, "## Analytics metric reconciliation", ANALYTICS)
    else:
        text = insert_before(text, "## Data and credentials", ANALYTICS)
    with README_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("README updated with analytics metric reconciliation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
