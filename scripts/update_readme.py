"""Keep the public README aligned with the implemented repository."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")

STATUS = """## Project status

The repository includes a reproducible Python environment, a documented business and data model,
deterministic synthetic source datasets, live-verified Snowflake infrastructure, and a Python
pipeline that validates, audits, and idempotently loads source records into the raw data layer.

The next implementation work will build tested dbt models across the staging, core, and analytics
layers. Power BI reporting and technician-note enrichment will follow.
"""

SNOWFLAKE = """## Snowflake infrastructure

The Snowflake setup creates an X-Small warehouse, a monthly resource monitor, five managed-access
schemas, four functional roles, future grants, and operations tables for ingestion and data-quality
audit records.

Setup and access checks are documented in `docs/snowflake_setup.md` and
`docs/snowflake_verification.md`. The verification record includes the completed live deployment and
least-privilege access checks.
"""

INGESTION = """## Python ingestion pipeline

The ingestion command validates all configured CSV files before connecting to Snowflake, separates
accepted and rejected rows, creates missing raw tables, and loads accepted records in batches. It
also writes run-level and dataset-level audit records. A deterministic record hash prevents
duplicate inserts when the same files are loaded again.

    python -m industrial_service_platform prepare-ingestion
    python -m industrial_service_platform test-snowflake
    python -m industrial_service_platform create-raw-tables
    python -m industrial_service_platform ingest

Connection setup, live verification, expected outputs, and common errors are documented in
`docs/ingestion_setup.md`.
"""


def replace_section(text: str, heading: str, replacement: str) -> str:
    """Replace a second-level Markdown section."""
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
    """Update implementation status and public usage sections."""
    text = README_PATH.read_text(encoding="utf-8")
    text = replace_section(text, "## Project status", STATUS)
    text = replace_section(text, "## Snowflake infrastructure", SNOWFLAKE)

    if "## Python ingestion pipeline" in text:
        text = replace_section(text, "## Python ingestion pipeline", INGESTION)
    else:
        text = insert_before(text, "## Data and credentials", INGESTION)

    README_PATH.write_text(text, encoding="utf-8")
    print("README updated with the Snowflake ingestion pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
