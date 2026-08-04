"""Calculate the independent KPI reference without connecting to Snowflake."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from industrial_service_platform.analytics.reference_metrics import compute_reference_metrics

CONFIG_PATH = Path("config/analytics_reconciliation.json")


def main() -> int:
    """Print and store the local reference metric set."""
    configuration: dict[str, Any] = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    reporting_as_of = datetime.fromisoformat(
        str(configuration["reporting_as_of"]).replace("Z", "+00:00")
    )
    metrics = compute_reference_metrics(
        Path(str(configuration["source_directory"])),
        reporting_as_of,
    )
    report = {
        "reporting_as_of": configuration["reporting_as_of"],
        "metrics": metrics,
    }
    output_path = Path("data/generated/python_reference_metrics.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
