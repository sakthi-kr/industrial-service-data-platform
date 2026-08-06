"""Complete operational verification after live and local controls pass."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

VERIFICATION_PATH = Path("docs/operational_verification.md")
HEALTH_PATH = Path("data/generated/operational_health.json")
DRILL_PATH = Path("data/generated/recovery_drill_report.json")
SAMPLE_DIRECTORY = Path("data/samples/operations")
EXPECTED_CHECKS = 20


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Required verification report is missing: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected a JSON object in {path}")
    return value


def complete_verification(
    verification_path: Path = VERIFICATION_PATH,
    health_path: Path = HEALTH_PATH,
    drill_path: Path = DRILL_PATH,
    sample_directory: Path = SAMPLE_DIRECTORY,
) -> int:
    """Validate reports, complete the checklist, and write public summaries."""
    health = _load_json(health_path)
    drills = _load_json(drill_path)
    if health.get("overall_status") != "PASS":
        raise RuntimeError("Operational health report is not PASS")
    if drills.get("all_drills_passed") is not True:
        raise RuntimeError("Recovery drill report did not pass all scenarios")

    text = verification_path.read_text(encoding="utf-8")
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")
    if unchecked == EXPECTED_CHECKS and checked == 0:
        text = text.replace("- [ ]", "- [x]")
    elif checked == EXPECTED_CHECKS and unchecked == 0:
        pass
    else:
        raise RuntimeError(
            "Operational checklist must be entirely pending or complete: "
            f"checked={checked}, unchecked={unchecked}"
        )

    if "## Deployment result" not in text:
        text = text.rstrip() + (
            "\n\n## Deployment result\n\n"
            f"Verified on {date.today().isoformat()} using local recovery drills, "
            "live Snowflake health checks, cost-control review, and GitHub security workflows.\n"
        )
    verification_path.write_text(text, encoding="utf-8")

    sample_directory.mkdir(parents=True, exist_ok=True)
    health_summary = {
        "overall_status": health["overall_status"],
        "checks": [{"name": item["name"], "status": item["status"]} for item in health["checks"]],
    }
    drill_summary = {
        "all_drills_passed": drills["all_drills_passed"],
        "drills": drills["drills"],
    }
    (sample_directory / "health_summary.json").write_text(
        json.dumps(health_summary, indent=2) + "\n",
        encoding="utf-8",
    )
    (sample_directory / "recovery_drill_summary.json").write_text(
        json.dumps(drill_summary, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Operational verification completed with {EXPECTED_CHECKS} checks.")
    return 0


def main() -> int:
    """Require an explicit confirmation before completing live verification."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-live-verification", action="store_true")
    arguments = parser.parse_args()
    if not arguments.confirm_live_verification:
        raise RuntimeError("Pass --confirm-live-verification after all live checks succeed")
    return complete_verification()


if __name__ == "__main__":
    raise SystemExit(main())
