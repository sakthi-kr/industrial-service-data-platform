"""Run live Snowflake operational checks and write a local health report."""

from __future__ import annotations

import json
from pathlib import Path

from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.health import evaluate_health
from industrial_service_platform.operations.snowflake import collect_operational_snapshot

CONFIG_PATH = Path("config/operational_health.json")


def main() -> int:
    """Collect, evaluate, persist, and print the platform health report."""
    config = OperationalConfig.from_json(CONFIG_PATH)
    snapshot = collect_operational_snapshot(config)
    report = evaluate_health(snapshot, config)
    rendered = json.dumps(report.to_dict(), indent=2)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    config.output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report.overall_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
