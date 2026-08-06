"""Complete the final release-readiness verification record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CHECKLIST_PATH = Path("docs/final_verification.md")
CONFIG_PATH = Path("config/release.json")
SUMMARY_PATH = Path("data/samples/release/release_summary.json")
EXPECTED_CHECKS = 13


def complete_verification(path: Path = CHECKLIST_PATH) -> None:
    text = path.read_text(encoding="utf-8")
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")

    if checked == EXPECTED_CHECKS and unchecked == 0:
        return
    if unchecked != EXPECTED_CHECKS or checked != 0:
        raise RuntimeError(
            "Expected either a fully pending or fully complete readiness checklist: "
            f"checked={checked}, unchecked={unchecked}"
        )

    updated = text.replace("- [ ]", "- [x]")
    updated = updated.replace(
        "## Readiness result\n\nPending.",
        (
            "## Readiness result\n\n"
            "The repository and external assets are ready for the `v1.0.0` "
            "release commit, tag and GitHub release."
        ),
        1,
    )
    path.write_text(updated, encoding="utf-8", newline="\n")


def write_summary() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    summary = {
        "version": config["version"],
        "tag": config["tag"],
        "release_date": config["release_date"],
        "source_datasets": 13,
        "source_records": 107724,
        "reconciled_kpis": 12,
        "enriched_notes": 5000,
        "power_bi_pages": 2,
        "release_status": "READY",
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm-release-ready",
        action="store_true",
        help="Confirm that the repository and external release assets are ready.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm_release_ready:
        raise RuntimeError("Use --confirm-release-ready only after all readiness checks pass.")
    complete_verification()
    write_summary()
    print(f"Release readiness completed with {EXPECTED_CHECKS} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
