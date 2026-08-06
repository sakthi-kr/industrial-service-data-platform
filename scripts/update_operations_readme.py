"""Update public README status and operational-control documentation safely."""

from __future__ import annotations

from pathlib import Path

README_PATH = Path("README.md")


def replace_section(text: str, heading: str, body: str) -> str:
    """Replace one Markdown section using heading boundaries."""
    marker = f"## {heading}\n"
    start = text.find(marker)
    if start < 0:
        raise RuntimeError(f"README section not found: {heading}")
    next_heading = text.find("\n## ", start + len(marker))
    end = len(text) if next_heading < 0 else next_heading + 1
    replacement = marker + body.rstrip() + "\n\n"
    return text[:start] + replacement + text[end:]


def insert_before_section(text: str, heading: str, content: str) -> str:
    """Insert content before a named section when it is not already present."""
    if content.splitlines()[0] in text:
        return text
    marker = f"## {heading}\n"
    index = text.find(marker)
    if index < 0:
        raise RuntimeError(f"README insertion section not found: {heading}")
    return text[:index] + content.rstrip() + "\n\n" + text[index:]


def main() -> int:
    """Describe completed operational controls without internal planning labels."""
    text = README_PATH.read_text(encoding="utf-8")
    status = (
        "The repository now contains the complete reproducible data workflow: deterministic "
        "industrial source data, live-verified Snowflake infrastructure, idempotent ingestion, "
        "tested dbt models, independently reconciled KPIs, a documented Power BI report, and "
        "evaluated technician-note enrichment. Operational health checks, recovery drills, "
        "cost controls, security workflows, and incident runbooks are also implemented.\n\n"
        "The remaining work is the final repository audit, versioned release, and portfolio-ready "
        "project summary."
    )
    text = replace_section(text, "Project status", status)
    operational = """## Operational controls
A live health command checks ingestion status, freshness, source and mart row counts, and data
quality. It also checks technician-note validity and warehouse cost settings. Recovery drills
prove that failed runs, stale data, rejection spikes, row-count drift, invalid enrichment outputs,
and warehouse misconfiguration are detected before publication.

    python scripts/run_recovery_drills.py
    python scripts/check_platform_health.py
    python scripts/validate_operational_assets.py

Incident response, recovery steps, security controls, and live verification are documented in
`docs/operations_runbook.md`, `docs/recovery_procedures.md`,
`docs/security_and_cost_controls.md`, and `docs/operational_verification.md`.
"""
    text = insert_before_section(text, "Data and credentials", operational)
    README_PATH.write_text(text, encoding="utf-8")
    print("README updated with operational controls.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
