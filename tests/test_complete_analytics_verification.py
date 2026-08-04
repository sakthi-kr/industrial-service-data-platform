from pathlib import Path

from pytest import MonkeyPatch

from scripts.complete_analytics_verification import EXPECTED_CHECKS, main


def test_completion_marks_expected_checklist(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    path = tmp_path / "verification.md"
    path.write_text("# Verification\n\n" + "- [ ] item\n" * EXPECTED_CHECKS, encoding="utf-8")
    monkeypatch.setattr("scripts.complete_analytics_verification.PATH", path)
    assert main() == 0
    text = path.read_text(encoding="utf-8")
    assert text.count("- [x]") == EXPECTED_CHECKS
    assert "## Deployment result" in text


def test_completion_is_idempotent(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    path = tmp_path / "verification.md"
    path.write_text("# Verification\n\n" + "- [x] item\n" * EXPECTED_CHECKS, encoding="utf-8")
    monkeypatch.setattr("scripts.complete_analytics_verification.PATH", path)
    assert main() == 0
