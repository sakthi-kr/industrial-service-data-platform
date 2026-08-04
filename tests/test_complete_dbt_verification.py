from pathlib import Path

from pytest import MonkeyPatch

from scripts.complete_dbt_verification import EXPECTED_CHECKS, main


def test_completion_script_marks_expected_checklist(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    path = docs / "dbt_verification.md"
    path.write_text("# Verification\n\n" + "- [ ] check\n" * EXPECTED_CHECKS, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["--date", "2026-08-04"]) == 0

    text = path.read_text(encoding="utf-8")
    assert text.count("- [x]") == EXPECTED_CHECKS
    assert "Verified against the live Snowflake account on 2026-08-04." in text


def test_completion_script_is_idempotent(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    path = docs / "dbt_verification.md"
    path.write_text("# Verification\n\n" + "- [x] check\n" * EXPECTED_CHECKS, encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main([]) == 0
    assert "## Deployment result" not in path.read_text(encoding="utf-8")
