from __future__ import annotations

import re
from pathlib import Path

from scripts.validate_dbt_project import main

PUBLIC_DBT_ROOTS = (
    Path("dbt/macros"),
    Path("dbt/models"),
    Path("dbt/snapshots"),
    Path("dbt/tests"),
)

PUBLIC_DBT_FILES = (
    Path("dbt/dbt_project.yml"),
    Path("dbt/profiles.example.yml"),
    Path("docs/dbt_model_design.md"),
    Path("docs/dbt_setup.md"),
)

TEXT_SUFFIXES = {
    ".sql",
    ".yml",
    ".yaml",
    ".md",
}


def public_text_files() -> list[Path]:
    """Return public dbt sources without generated runtime files."""
    files = [path for path in PUBLIC_DBT_FILES if path.is_file()]

    for root in PUBLIC_DBT_ROOTS:
        if not root.exists():
            continue

        files.extend(
            path
            for path in root.rglob("*")
            if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES
        )

    return sorted(set(files))


def test_dbt_static_validation_passes() -> None:
    assert main() == 0


def test_profiles_example_uses_environment_variables() -> None:
    text = Path("dbt/profiles.example.yml").read_text(encoding="utf-8")

    assert "SNOWFLAKE_ACCOUNT" in text
    assert "SNOWFLAKE_PASSWORD" in text
    assert "DBT_SNOWFLAKE_ROLE" in text
    assert "ISP_TRANSFORMER" in text


def test_public_dbt_files_do_not_contain_numbered_planning_labels() -> None:
    forbidden_word = "ph" + "ase"

    pattern = re.compile(
        rf"{forbidden_word}[ _-]*[0-9]+",
        re.IGNORECASE,
    )

    failures: list[str] = []

    for path in public_text_files():
        if pattern.search(path.as_posix()):
            failures.append(str(path))
            continue

        text = path.read_text(encoding="utf-8")

        if pattern.search(text):
            failures.append(str(path))

    assert not failures, f"Numbered planning labels found in dbt files: {failures}"
