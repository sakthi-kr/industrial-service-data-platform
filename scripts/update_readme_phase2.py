"""Update the README after the Phase 2 gate has passed."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")

STATUS_TEXT = """## Project status

Phases 0, 1, and 2 are complete. The repository now includes the development setup, documented
business and data model, deterministic synthetic source datasets, schema and relationship checks,
controlled invalid examples, tracked samples, and reproducibility manifests.

The next phase will create the Snowflake database, schemas, warehouse, roles, and grants. dbt,
Power BI, and technician-note enrichment will be added after the ingestion and warehouse layers are
working.
"""

GENERATION_TEXT = """## Synthetic data generation

The default configuration generates the full ERP-, CRM-, monitoring-, and field-service-style
source files locally. Generated files are excluded from Git; small samples and validation metadata
are kept in `data/samples/phase2/`.

    python -m industrial_service_platform generate-data
    python -m industrial_service_platform validate-data

The generator uses a fixed seed and reporting timestamp. Repeated runs with the same configuration
produce the same file content and SHA-256 hashes.
"""


def main() -> int:
    text = README_PATH.read_text(encoding="utf-8")
    updated = _replace_section(text, "## Project status", STATUS_TEXT.rstrip())

    if "## Synthetic data generation" not in updated:
        markers = ["## Project phases", "## Data and credentials", "## Licence"]
        marker = next((item for item in markers if item in updated), None)
        if marker is None:
            updated = updated.rstrip() + "\n\n" + GENERATION_TEXT
        else:
            updated = updated.replace(marker, f"{GENERATION_TEXT}\n{marker}", 1)

    README_PATH.write_text(updated, encoding="utf-8")
    print("README updated to show Phase 2 complete.")
    return 0


def _replace_section(text: str, heading: str, replacement: str) -> str:
    start = text.find(heading)
    if start == -1:
        raise RuntimeError(f"README section was not found: {heading}")
    next_heading = text.find("\n## ", start + len(heading))
    if next_heading == -1:
        return text[:start] + replacement + "\n"
    return text[:start] + replacement + "\n\n" + text[next_heading + 1 :]


if __name__ == "__main__":
    raise SystemExit(main())
