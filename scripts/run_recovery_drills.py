"""Run deterministic, non-destructive recovery-control drills."""

from __future__ import annotations

import json
from pathlib import Path

from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.drills import run_recovery_drills

CONFIG_PATH = Path("config/operational_health.json")


def main() -> int:
    """Run all drills and write a local evidence report."""
    config = OperationalConfig.from_json(CONFIG_PATH)
    results = run_recovery_drills(config)
    report = {
        "all_drills_passed": all(result.detected for result in results),
        "drills": [result.to_dict() for result in results],
    }
    rendered = json.dumps(report, indent=2)
    config.recovery_output_path.parent.mkdir(parents=True, exist_ok=True)
    config.recovery_output_path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["all_drills_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
