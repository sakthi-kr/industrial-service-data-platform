from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIPPED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "generated",
}
TEXT_SUFFIXES = {".json", ".md", ".py", ".sql", ".toml", ".txt", ".yaml", ".yml"}


def public_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIPPED_DIRECTORIES for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            files.append(path)
    return files


def test_internal_numbered_planning_labels_are_not_public() -> None:
    forbidden_word = "ph" + "ase"
    pattern = re.compile(rf"{forbidden_word}[ _-]*[0-9]+", re.IGNORECASE)

    failures: list[str] = []
    for path in public_files():
        relative = path.relative_to(ROOT)
        if pattern.search(relative.as_posix()):
            failures.append(str(relative))
            continue
        text = path.read_text(encoding="utf-8")
        if pattern.search(text):
            failures.append(str(relative))

    assert not failures, f"Internal planning labels found in public files: {failures}"
