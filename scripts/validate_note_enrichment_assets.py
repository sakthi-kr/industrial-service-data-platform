"""Validate tracked technician-note enrichment assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

CONFIG_PATH = Path("config/note_enrichment.json")
VERIFICATION_PATH = Path("docs/note_enrichment_verification.md")
EXPECTED_CHECKS = 17

REQUIRED_FILES = (
    CONFIG_PATH,
    Path("docs/note_enrichment_design.md"),
    Path("docs/note_enrichment_setup.md"),
    VERIFICATION_PATH,
    Path("scripts/build_note_enrichment_dataset.py"),
    Path("scripts/train_note_enrichment.py"),
    Path("scripts/publish_note_enrichment.py"),
    Path("scripts/complete_note_enrichment_verification.py"),
    Path("sql/note_enrichment/00_verify_published_results.sql"),
    Path("sql/note_enrichment/01_verify_enrichment_quality.sql"),
    Path("sql/note_enrichment/02_verify_analyst_access.sql"),
    Path("dbt/models/staging/_enrichment_sources.yml"),
    Path("dbt/models/marts/mart_technician_note_enrichment.sql"),
    Path("dbt/tests/assert_note_enrichment_output_valid.sql"),
    Path("dbt/tests/assert_note_enrichment_confidence_bounded.sql"),
)


def checklist_state(text: str) -> str:
    """Return whether the verification checklist is pending or complete."""
    unchecked = text.count("- [ ]")
    checked = text.count("- [x]")
    total = unchecked + checked
    if total != EXPECTED_CHECKS:
        raise RuntimeError(f"Expected {EXPECTED_CHECKS} note-enrichment checks, found {total}")
    if unchecked == EXPECTED_CHECKS:
        return "pending"
    if checked == EXPECTED_CHECKS:
        return "complete"
    raise RuntimeError(
        "Note-enrichment checklist is partially completed: "
        f"checked={checked}, unchecked={unchecked}"
    )


def main() -> int:
    """Validate all tracked note-enrichment assets."""
    missing = [str(path) for path in REQUIRED_FILES if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing note-enrichment assets: {missing}")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if config["model_version"] != "tfidf-logreg-v1":
        raise RuntimeError("Unexpected note-enrichment model version")
    if int(config["batch_size"]) < 1:
        raise RuntimeError("Invalid Snowflake publication batch size")

    thresholds = config["minimum_metrics"]
    expected_thresholds = {
        "fault_macro_f1",
        "priority_macro_f1",
        "component_accuracy",
        "structured_output_validity_rate",
    }
    if set(thresholds) != expected_thresholds:
        raise RuntimeError("Unexpected note-enrichment threshold set")

    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    if '"scikit-learn==1.7.2"' not in pyproject:
        raise RuntimeError("Python 3.10-compatible scikit-learn pin is missing")

    verification = VERIFICATION_PATH.read_text(encoding="utf-8")
    state = checklist_state(verification)
    if state == "complete":
        required_evidence = (
            Path("data/samples/note_enrichment/evaluation_summary.json"),
            Path("data/samples/note_enrichment/sample_predictions.csv"),
        )
        evidence_missing = [str(path) for path in required_evidence if not path.is_file()]
        if evidence_missing:
            raise RuntimeError(f"Completed verification lacks public evidence: {evidence_missing}")
        if "## Deployment result" not in verification:
            raise RuntimeError("Completed verification lacks a deployment result")

    forbidden = re.compile(r"phase[ _-]*[0-9]+", re.IGNORECASE)
    public_paths = [
        *Path("docs").glob("note_enrichment*.md"),
        *Path("src/industrial_service_platform/enrichment").glob("*.py"),
        *Path("scripts").glob("*note_enrichment*.py"),
    ]
    failures = [
        str(path)
        for path in public_paths
        if forbidden.search(path.as_posix()) or forbidden.search(path.read_text(encoding="utf-8"))
    ]
    if failures:
        raise RuntimeError(f"Numbered planning labels found: {failures}")

    for path in REQUIRED_FILES:
        text = path.read_text(encoding="utf-8")
        if not text.endswith("\n"):
            raise RuntimeError(f"File does not end with a newline: {path}")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            raise RuntimeError(f"Trailing whitespace found in {path}")

    print(
        "Note-enrichment asset validation passed: "
        f"model={config['model_version']}, checks={EXPECTED_CHECKS}, state={state}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
