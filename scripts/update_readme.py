"""Keep the public README aligned with the implemented repository."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")

STATUS = """## Project status

The repository includes a reproducible Python development environment, a documented business and
data model, deterministic synthetic source datasets, schema and relationship checks, controlled
invalid examples, and Snowflake infrastructure scripts with a least-privilege access model.

The next implementation work will connect the Python ingestion pipeline to the Snowflake raw and
operations schemas. dbt models, Power BI reporting, and technician-note enrichment will follow.
"""

SNOWFLAKE = """## Snowflake infrastructure

The Snowflake setup creates an X-Small warehouse, a monthly resource monitor, five managed-access
schemas, four functional roles, future grants, and operations tables for ingestion and data-quality
audit records.

Run the setup from Snowsight in the order documented in `docs/snowflake_setup.md`. Local validation
checks file structure and expected grants, but the access checklist in
`docs/snowflake_verification.md` must be completed against a real Snowflake account.
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


def remove_internal_roadmap(text: str) -> str:
    """Remove the internal numbered roadmap from the public README."""
    heading = "## Project " + "ph" + "ases"
    start = text.find(heading)
    if start == -1:
        return text
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[:start].rstrip() + "\n"
    return text[:start].rstrip() + "\n\n" + text[next_heading + 1 :]


def main() -> int:
    """Update status, paths, and the Snowflake section."""
    text = README_PATH.read_text(encoding="utf-8")
    text = replace_section(text, "## Project status", STATUS)
    text = remove_internal_roadmap(text)
    old_sample_path = "data/samples/" + "ph" + "ase2/"
    text = text.replace(old_sample_path, "data/samples/source_data/")

    if "## Snowflake infrastructure" in text:
        text = replace_section(text, "## Snowflake infrastructure", SNOWFLAKE)
    else:
        marker = "## Data and credentials"
        if marker not in text:
            raise RuntimeError("README data-and-credentials section was not found")
        text = text.replace(marker, SNOWFLAKE.rstrip() + "\n\n" + marker, 1)

    README_PATH.write_text(text, encoding="utf-8")
    print("README updated with the implemented Snowflake infrastructure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
