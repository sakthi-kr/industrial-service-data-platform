"""Validate tracked Power BI report assets without requiring Power BI Desktop."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(".")
THEME_PATH = ROOT / "dashboards/power_bi/industrial_service_theme.json"
DAX_PATH = ROOT / "dashboards/power_bi/dax_measures.dax"
MODEL_PATH = ROOT / "dashboards/power_bi/model_relationships.md"
SPEC_PATH = ROOT / "dashboards/power_bi/report_build_spec.md"
SETUP_PATH = ROOT / "docs/power_bi_setup.md"
VERIFICATION_PATH = ROOT / "docs/power_bi_verification.md"
EVIDENCE_PATHS = (
    ROOT / "dashboards/power_bi/screenshots/service_operations_overview.png",
    ROOT / "dashboards/power_bi/screenshots/asset_customer_analysis.png",
    ROOT / "dashboards/power_bi/exports/industrial_service_dashboard.pdf",
)
EXPECTED_VERIFICATION_CHECKS = 15

EXPECTED_MEASURES = {
    "Cases",
    "Open Cases",
    "Critical Open Cases",
    "Resolved Cases",
    "Response SLA %",
    "Resolution SLA %",
    "Mean Resolution Hours",
    "Service Cost EUR",
    "Downtime Hours",
    "Asset Count",
    "High-Risk Assets",
    "Asset Service Cost EUR",
    "Asset Downtime Hours",
    "Critical Alerts",
    "Customer Count",
    "KPI Median Resolution Hours",
    "KPI First-Time-Fix %",
    "KPI Repeat Failure %",
}


def measure_names(text: str) -> set[str]:
    """Read DAX measure names from top-level assignment lines."""
    return {
        line[:-2].strip()
        for line in text.splitlines()
        if line.endswith(" =") and not line.lstrip().startswith("--")
    }


def verification_state(text: str) -> str:
    """Return whether the checklist is pending or complete."""
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")
    total = unchecked + checked

    if total != EXPECTED_VERIFICATION_CHECKS:
        raise RuntimeError(
            "Expected exactly "
            f"{EXPECTED_VERIFICATION_CHECKS} Power BI verification items, "
            f"found {total}"
        )

    if unchecked == EXPECTED_VERIFICATION_CHECKS:
        return "pending"

    if checked == EXPECTED_VERIFICATION_CHECKS:
        return "complete"

    raise RuntimeError(
        "Power BI verification checklist is partially completed: "
        f"checked={checked}, unchecked={unchecked}"
    )


def main() -> int:
    """Validate all non-binary Power BI assets."""
    required = [
        THEME_PATH,
        DAX_PATH,
        MODEL_PATH,
        SPEC_PATH,
        SETUP_PATH,
        VERIFICATION_PATH,
        ROOT / "sql/power_bi/00_verify_dashboard_sources.sql",
        ROOT / "sql/power_bi/01_verify_dynamic_measures.sql",
        ROOT / "sql/power_bi/02_verify_analyst_access.sql",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing Power BI assets: {missing}")

    theme = json.loads(THEME_PATH.read_text(encoding="utf-8"))
    colors = theme.get("dataColors")
    if theme.get("name") != "Industrial Service Operations":
        raise RuntimeError("Unexpected Power BI theme name")
    if not isinstance(colors, list) or len(colors) < 6:
        raise RuntimeError("Power BI theme needs at least six data colors")

    dax_text = DAX_PATH.read_text(encoding="utf-8")
    actual_measures = measure_names(dax_text)
    if actual_measures != EXPECTED_MEASURES:
        raise RuntimeError(
            "Unexpected DAX measure set: "
            f"missing={sorted(EXPECTED_MEASURES - actual_measures)}, "
            f"extra={sorted(actual_measures - EXPECTED_MEASURES)}"
        )

    model_text = MODEL_PATH.read_text(encoding="utf-8")
    for table in (
        "MART_SERVICE_OPERATIONS",
        "MART_ASSET_RELIABILITY",
        "MART_CUSTOMER_PERFORMANCE",
        "MART_KPI_SUMMARY",
    ):
        if table not in model_text:
            raise RuntimeError(f"Power BI model documentation is missing {table}")

    verification_text = VERIFICATION_PATH.read_text(encoding="utf-8")
    state = verification_state(verification_text)

    if state == "complete":
        missing_evidence = [str(path) for path in EVIDENCE_PATHS if not path.is_file()]
        if missing_evidence:
            raise RuntimeError(
                f"Completed Power BI verification is missing evidence files: {missing_evidence}"
            )

        if "## Deployment result" not in verification_text:
            raise RuntimeError("Completed Power BI verification is missing its deployment result")

    for path in required:
        text = path.read_text(encoding="utf-8")

        if not text.endswith("\n"):
            raise RuntimeError(f"File does not end with a newline: {path}")

        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            raise RuntimeError(f"Trailing whitespace found in {path}")

    print(
        "Power BI asset validation passed: "
        f"{len(EXPECTED_MEASURES)} measures, "
        f"{EXPECTED_VERIFICATION_CHECKS} verification checks, "
        f"state={state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
