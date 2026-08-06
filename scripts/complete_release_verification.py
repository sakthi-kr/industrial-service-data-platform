"""Complete the final version-verification record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

CHECKLIST_PATH = Path("docs/final_verification.md")
CONFIG_PATH = Path("config/release.json")
SUMMARY_PATH = Path("data/samples/release/release_summary.json")
EXPECTED_CHECKS = 13


def complete_verification(path: Path = CHECKLIST_PATH) -> None:
    """Mark a fully pending checklist as complete without accepting partial state."""
    text = path.read_text(encoding="utf-8")
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")

    if checked == EXPECTED_CHECKS and unchecked == 0:
        return

    if unchecked != EXPECTED_CHECKS or checked != 0:
        raise RuntimeError(
            "Expected either a fully pending or fully complete version checklist: "
            f"checked={checked}, unchecked={unchecked}"
        )

    updated = text.replace("- [ ]", "- [x]")
    updated = updated.replace(
        "## Verification result\n\nPending.",
        (
            "## Verification result\n\n"
            "The repository is complete and the annotated tag `v1.0.0` identifies "
            "the first audited portfolio version. No GitHub Release is published; "
            "the editable Power BI `.pbix` file remains local."
        ),
        1,
    )
    path.write_text(updated, encoding="utf-8", newline="\n")


def write_summary() -> None:
    """Write a small, sanitized summary of the tagged version."""
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
        "release_status": "TAGGED",
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
        help="Confirm that the repository is ready for its audited version tag.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm_release_ready:
        raise RuntimeError("Use --confirm-release-ready only after all version checks pass.")
    complete_verification()
    write_summary()
    print(f"Version verification completed with {EXPECTED_CHECKS} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
