import json
from pathlib import Path

from pytest import MonkeyPatch

from scripts import complete_release_verification as module


def test_complete_verification_marks_all_items(tmp_path: Path) -> None:
    path = tmp_path / "verification.md"
    path.write_text(
        "# Verify\n\n"
        + "\n".join(f"- [ ] item {index}" for index in range(13))
        + "\n\n## Readiness result\n\nPending.\n",
        encoding="utf-8",
    )

    module.complete_verification(path)
    text = path.read_text(encoding="utf-8")

    assert text.count("- [x]") == 13
    assert "ready for the `v1.0.0`" in text


def test_write_summary_creates_sanitized_file(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    config = tmp_path / "release.json"
    summary = tmp_path / "release_summary.json"
    config.write_text(
        '{"version":"1.0.0","tag":"v1.0.0","release_date":"2026-08-06"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "CONFIG_PATH", config)
    monkeypatch.setattr(module, "SUMMARY_PATH", summary)

    module.write_summary()
    data = json.loads(summary.read_text(encoding="utf-8"))

    assert data["release_status"] == "READY"
    assert data["source_records"] == 107724
    assert "account" not in data
