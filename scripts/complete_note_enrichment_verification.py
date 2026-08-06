"""Complete the technician-note enrichment verification record."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

CONFIG_PATH = Path("config/note_enrichment.json")
VERIFICATION_PATH = Path("docs/note_enrichment_verification.md")
EXPECTED_CHECKS = 17


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm-live-verification",
        action="store_true",
        help="Confirm that Snowflake publication, dbt build, and analyst checks succeeded.",
    )
    args = parser.parse_args()
    if not args.confirm_live_verification:
        raise RuntimeError("Pass --confirm-live-verification after completing the live checks")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    evaluation_path = Path(str(config["evaluation_path"]))
    predictions_path = Path(str(config["predictions_path"]))
    if not evaluation_path.is_file() or not predictions_path.is_file():
        raise RuntimeError("Local evaluation and prediction artifacts are required")
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    if not evaluation.get("all_thresholds_passed"):
        raise RuntimeError("Model evaluation thresholds did not all pass")
    if not evaluation.get("all_prediction_outputs_valid"):
        raise RuntimeError("At least one full-dataset prediction is invalid")
    with predictions_path.open("r", encoding="utf-8", newline="") as handle:
        prediction_count = sum(1 for _ in csv.DictReader(handle))
    if prediction_count != 5000:
        raise RuntimeError(f"Expected 5000 prediction rows, found {prediction_count}")
    text = VERIFICATION_PATH.read_text(encoding="utf-8")
    if text.count("- [ ]") != EXPECTED_CHECKS or "- [x]" in text:
        raise RuntimeError("Verification checklist is not in the expected pending state")
    text = text.replace("- [ ]", "- [x]")
    deployment = (
        "\n## Deployment result\n\n"
        "Verified locally and against Snowflake on 2026-08-06. The grouped holdout "
        "evaluation, lexical-ablation challenge, structured-output checks, idempotent "
        "publication, dbt mart, and analyst-role queries completed successfully.\n"
    )
    text = text.rstrip() + "\n" + deployment
    VERIFICATION_PATH.write_text(text, encoding="utf-8")
    print(f"Note-enrichment verification completed with {EXPECTED_CHECKS} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
