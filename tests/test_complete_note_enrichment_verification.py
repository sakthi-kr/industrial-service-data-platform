import csv
import json
import sys
from pathlib import Path

import pytest

import scripts.complete_note_enrichment_verification as completion


def test_completion_requires_explicit_live_confirmation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "argv", ["complete_note_enrichment_verification.py"])
    with pytest.raises(RuntimeError, match="confirm-live-verification"):
        completion.main()


def test_completion_marks_all_checks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evaluation = tmp_path / "evaluation.json"
    predictions = tmp_path / "predictions.csv"
    verification = tmp_path / "verification.md"
    config = tmp_path / "config.json"
    evaluation.write_text(
        json.dumps(
            {
                "all_thresholds_passed": True,
                "all_prediction_outputs_valid": True,
            }
        ),
        encoding="utf-8",
    )
    with predictions.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["note_id"])
        writer.writeheader()
        writer.writerows({"note_id": str(index)} for index in range(5000))
    verification.write_text(
        "# Verification\n\n" + "- [ ] item\n" * 17,
        encoding="utf-8",
    )
    config.write_text(
        json.dumps(
            {
                "evaluation_path": str(evaluation),
                "predictions_path": str(predictions),
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(completion, "CONFIG_PATH", config)
    monkeypatch.setattr(completion, "VERIFICATION_PATH", verification)
    monkeypatch.setattr(
        sys,
        "argv",
        ["complete_note_enrichment_verification.py", "--confirm-live-verification"],
    )
    assert completion.main() == 0
    text = verification.read_text(encoding="utf-8")
    assert text.count("- [x]") == 17
    assert "## Deployment result" in text
