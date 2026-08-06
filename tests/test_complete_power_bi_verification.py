from pathlib import Path

import pytest

from scripts.complete_power_bi_verification import complete_verification


def checklist_text() -> str:
    return (
        "# Power BI verification record\n\n"
        + "\n".join(f"- [ ] Check {index}" for index in range(1, 16))
        + "\n"
    )


def test_completion_requires_all_evidence_files(tmp_path: Path) -> None:
    checklist = tmp_path / "verification.md"
    checklist.write_text(checklist_text(), encoding="utf-8")

    with pytest.raises(RuntimeError, match="Missing Power BI evidence"):
        complete_verification(
            checklist,
            (
                tmp_path / "page1.png",
                tmp_path / "page2.png",
                tmp_path / "report.pdf",
            ),
        )


def test_completion_marks_all_checks(tmp_path: Path) -> None:
    checklist = tmp_path / "verification.md"
    checklist.write_text(checklist_text(), encoding="utf-8")
    evidence = (
        tmp_path / "page1.png",
        tmp_path / "page2.png",
        tmp_path / "report.pdf",
    )
    for path in evidence:
        path.write_bytes(b"evidence")

    complete_verification(checklist, evidence)
    text = checklist.read_text(encoding="utf-8")

    assert text.count("- [x]") == 15
    assert "- [ ]" not in text
    assert "## Deployment result" in text
