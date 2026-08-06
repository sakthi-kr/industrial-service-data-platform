import json
from pathlib import Path

from scripts.complete_operational_verification import (
    EXPECTED_CHECKS,
    complete_verification,
)


def _verification_text() -> str:
    checklist = "\n".join(f"- [ ] Check {index}" for index in range(EXPECTED_CHECKS))
    return f"# Operational verification\n\n{checklist}\n"


def test_completion_marks_checks_and_writes_public_summaries(tmp_path: Path) -> None:
    verification = tmp_path / "verification.md"
    health = tmp_path / "health.json"
    drills = tmp_path / "drills.json"
    samples = tmp_path / "samples"
    verification.write_text(_verification_text(), encoding="utf-8")
    health.write_text(
        json.dumps(
            {
                "overall_status": "PASS",
                "checks": [{"name": "example", "status": "PASS"}],
            }
        ),
        encoding="utf-8",
    )
    drills.write_text(
        json.dumps(
            {
                "all_drills_passed": True,
                "drills": [
                    {
                        "scenario": "example",
                        "expected_failed_check": "example",
                        "detected": True,
                        "overall_status": "FAIL",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert complete_verification(verification, health, drills, samples) == 0
    text = verification.read_text(encoding="utf-8")
    assert text.count("- [x]") == EXPECTED_CHECKS
    assert "## Deployment result" in text
    assert (samples / "health_summary.json").is_file()
    assert (samples / "recovery_drill_summary.json").is_file()


def test_completion_is_idempotent(tmp_path: Path) -> None:
    verification = tmp_path / "verification.md"
    health = tmp_path / "health.json"
    drills = tmp_path / "drills.json"
    samples = tmp_path / "samples"
    verification.write_text(_verification_text(), encoding="utf-8")
    health.write_text(
        json.dumps({"overall_status": "PASS", "checks": []}),
        encoding="utf-8",
    )
    drills.write_text(
        json.dumps({"all_drills_passed": True, "drills": []}),
        encoding="utf-8",
    )

    complete_verification(verification, health, drills, samples)
    complete_verification(verification, health, drills, samples)

    text = verification.read_text(encoding="utf-8")
    assert text.count("## Deployment result") == 1
