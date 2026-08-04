"""Static validation for analytics reconciliation assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

from industrial_service_platform.analytics.reference_metrics import KPI_NAMES

EXPECTED_FILES = (
    Path("config/analytics_reconciliation.json"),
    Path("dbt/models/intermediate/int_case_first_time_fix.sql"),
    Path("dbt/models/intermediate/int_case_repeat_failure.sql"),
    Path("dbt/models/intermediate/int_asset_downtime.sql"),
    Path("dbt/models/marts/mart_kpi_summary.sql"),
    Path("dbt/tests/assert_kpi_summary_single_row.sql"),
    Path("dbt/tests/assert_kpi_rates_bounded.sql"),
    Path("dbt/tests/assert_kpi_metrics_non_negative.sql"),
    Path("docs/analytics_reconciliation.md"),
    Path("docs/analytics_verification.md"),
    Path("scripts/calculate_reference_metrics.py"),
    Path("scripts/reconcile_analytics.py"),
    Path("sql/analytics/00_verify_kpi_summary.sql"),
    Path("sql/analytics/01_verify_kpi_populations.sql"),
    Path("sql/analytics/02_verify_kpi_constraints.sql"),
)


def main() -> int:
    """Validate configuration, files, SQL references, and public wording."""
    missing = [str(path) for path in EXPECTED_FILES if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing analytics assets: {missing}")

    config = json.loads(EXPECTED_FILES[0].read_text(encoding="utf-8"))
    tolerance_names = tuple(config["tolerances"])
    if tolerance_names != KPI_NAMES:
        raise RuntimeError(
            f"Configured KPI names do not match the Python reference order: {tolerance_names}"
        )

    mart_text = Path("dbt/models/marts/mart_kpi_summary.sql").read_text(encoding="utf-8")
    missing_metrics = [name for name in KPI_NAMES if name not in mart_text]
    if missing_metrics:
        raise RuntimeError(f"KPI mart is missing metrics: {missing_metrics}")

    for path in EXPECTED_FILES:
        text = path.read_text(encoding="utf-8")
        if text.count("{{") != text.count("}}"):
            raise RuntimeError(f"Unbalanced Jinja expressions in {path}")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            raise RuntimeError(f"Trailing whitespace in {path}")

    forbidden_word = "ph" + "ase"
    pattern = re.compile(rf"{forbidden_word}[ _-]*[0-9]+", re.IGNORECASE)
    public_paths = [
        *EXPECTED_FILES,
        Path("src/industrial_service_platform/analytics/reference_metrics.py"),
    ]
    failures = [
        str(path) for path in public_paths if pattern.search(path.read_text(encoding="utf-8"))
    ]
    if failures:
        raise RuntimeError(f"Numbered planning labels found: {failures}")

    print(f"Analytics asset validation passed: {len(KPI_NAMES)} reconciled metrics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
