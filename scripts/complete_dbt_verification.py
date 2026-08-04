"""Record a completed live dbt verification after the user checks every result."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

VERIFICATION_PATH = Path("docs/dbt_verification.md")
EXPECTED_CHECKS = 15


def build_parser() -> argparse.ArgumentParser:
    """Create the small command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date",
        default=date.today().isoformat(),
        help="Verification date in YYYY-MM-DD format; defaults to today.",
    )
    return parser


def main(arguments: list[str] | None = None) -> int:
    """Mark every verified item complete and append a deployment record once."""
    args = build_parser().parse_args(arguments)
    path = VERIFICATION_PATH
    text = path.read_text(encoding="utf-8")
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")

    if unchecked == 0 and checked == EXPECTED_CHECKS:
        print("dbt verification record is already complete.")
        return 0
    if unchecked != EXPECTED_CHECKS or checked != 0:
        raise RuntimeError(
            "Expected exactly "
            f"{EXPECTED_CHECKS} unchecked items and no checked items; "
            f"found unchecked={unchecked}, checked={checked}."
        )

    text = text.replace("- [ ]", "- [x]")
    deployment = (
        "\n## Deployment result\n\n"
        f"Verified against the live Snowflake account on {args.date}. "
        "The full build, data tests, asset snapshot, reporting marts, "
        "analyst access, and generated lineage documentation completed "
        "successfully.\n"
    )
    if "## Deployment result" not in text:
        text = text.rstrip() + "\n" + deployment

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(f"dbt verification record completed with {EXPECTED_CHECKS} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
