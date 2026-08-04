"""Static checks for the dbt project that do not require Snowflake credentials."""

from __future__ import annotations

import re
from pathlib import Path

DBT_ROOT = Path("dbt")
EXPECTED_STAGING_MODELS = 13
EXPECTED_INTERMEDIATE_MODELS = 5
EXPECTED_CORE_MODELS = 12
EXPECTED_MART_MODELS = 4
EXPECTED_SINGULAR_TESTS = 11

SQL_SOURCE_DIRECTORIES = (
    DBT_ROOT / "macros",
    DBT_ROOT / "models",
    DBT_ROOT / "snapshots",
    DBT_ROOT / "tests",
)


def sql_files(directory: Path) -> list[Path]:
    """Return sorted SQL files directly below a directory."""
    return sorted(directory.glob("*.sql"))


def project_sql_files() -> list[Path]:
    """Return tracked dbt SQL sources, excluding generated directories."""
    files: list[Path] = []

    for directory in SQL_SOURCE_DIRECTORIES:
        if directory.exists():
            files.extend(path for path in directory.rglob("*.sql") if path.is_file())

    return sorted(files)


def assert_balanced_jinja(path: Path) -> None:
    """Catch truncated Jinja blocks before dbt is invoked."""
    text = path.read_text(encoding="utf-8")

    if text.count("{{") != text.count("}}"):
        raise RuntimeError(f"Unbalanced Jinja expression delimiters in {path}")

    statement_starts = text.count("{%-") + text.count("{% ")
    statement_ends = text.count("-%}") + text.count(" %}")

    if statement_starts != statement_ends:
        raise RuntimeError(f"Unbalanced Jinja statement delimiters in {path}")


def validate_model_references() -> None:
    """Confirm every ref and source call points to a declared resource."""
    model_paths = [
        *DBT_ROOT.glob("models/**/*.sql"),
        *DBT_ROOT.glob("snapshots/*.sql"),
    ]
    model_names = {path.stem for path in model_paths}

    source_text = (DBT_ROOT / "models/staging/_sources.yml").read_text(encoding="utf-8")

    source_names = set(
        re.findall(
            r"^      - name: ([a-z0-9_]+)$",
            source_text,
            re.MULTILINE,
        )
    )

    missing_refs: list[str] = []
    missing_sources: list[str] = []

    for path in model_paths:
        text = path.read_text(encoding="utf-8")

        for reference in re.findall(
            r"ref\(['\"]([^'\"]+)['\"]\)",
            text,
        ):
            if reference not in model_names:
                missing_refs.append(f"{path}: {reference}")

        for source_name, table_name in re.findall(
            (
                r"source\(['\"]([^'\"]+)['\"],"
                r"\s*['\"]([^'\"]+)['\"]\)"
            ),
            text,
        ):
            if source_name != "raw" or table_name not in source_names:
                missing_sources.append(f"{path}: {source_name}.{table_name}")

    if missing_refs:
        raise RuntimeError(f"Unknown dbt refs: {missing_refs}")

    if missing_sources:
        raise RuntimeError(f"Unknown dbt sources: {missing_sources}")


def main() -> int:
    """Validate expected project assets and configuration."""
    required = [
        DBT_ROOT / "dbt_project.yml",
        DBT_ROOT / "profiles.example.yml",
        DBT_ROOT / "models/staging/_sources.yml",
        DBT_ROOT / "models/core/_core_models.yml",
        DBT_ROOT / "models/marts/_marts.yml",
        DBT_ROOT / "snapshots/snap_asset_history.sql",
        DBT_ROOT / "macros/generate_schema_name.sql",
        DBT_ROOT / "macros/test_row_count_equals.sql",
    ]

    missing = [str(path) for path in required if not path.is_file()]

    if missing:
        raise RuntimeError(f"Missing required dbt files: {missing}")

    counts = {
        "staging": len(sql_files(DBT_ROOT / "models/staging")),
        "intermediate": len(sql_files(DBT_ROOT / "models/intermediate")),
        "core": len(sql_files(DBT_ROOT / "models/core")),
        "marts": len(sql_files(DBT_ROOT / "models/marts")),
        "tests": len(sql_files(DBT_ROOT / "tests")),
    }

    expected = {
        "staging": EXPECTED_STAGING_MODELS,
        "intermediate": EXPECTED_INTERMEDIATE_MODELS,
        "core": EXPECTED_CORE_MODELS,
        "marts": EXPECTED_MART_MODELS,
        "tests": EXPECTED_SINGULAR_TESTS,
    }

    if counts != expected:
        raise RuntimeError(f"Unexpected dbt SQL file counts: actual={counts}, expected={expected}")

    gitignore = Path(".gitignore")

    if gitignore.exists():
        ignore_text = gitignore.read_text(encoding="utf-8")

        if "dbt/profiles.yml" not in ignore_text:
            raise RuntimeError("dbt/profiles.yml is not excluded by .gitignore")

    project_text = (DBT_ROOT / "dbt_project.yml").read_text(encoding="utf-8")

    expected_version = 'require-dbt-version: [">=1.12.0", "<2.0.0"]'

    if expected_version not in project_text:
        raise RuntimeError("dbt Core version range is missing or unexpected")

    profile_text = (DBT_ROOT / "profiles.example.yml").read_text(encoding="utf-8")

    required_environment_names = {
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
        "SNOWFLAKE_WAREHOUSE",
        "SNOWFLAKE_DATABASE",
        "DBT_SNOWFLAKE_ROLE",
    }

    missing_environment_names = sorted(
        name for name in required_environment_names if name not in profile_text
    )

    if missing_environment_names:
        raise RuntimeError(
            f"dbt profile is missing environment variables: {missing_environment_names}"
        )

    schema_macro = (DBT_ROOT / "macros/generate_schema_name.sql").read_text(encoding="utf-8")

    if "custom_schema_name | trim" not in schema_macro:
        raise RuntimeError("Custom schema routing macro is incomplete")

    for path in project_sql_files():
        assert_balanced_jinja(path)

    validate_model_references()

    print(
        "dbt project validation passed: "
        f"{counts['staging']} staging, "
        f"{counts['core']} core, "
        f"{counts['marts']} mart models, "
        f"{counts['tests']} singular tests"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
