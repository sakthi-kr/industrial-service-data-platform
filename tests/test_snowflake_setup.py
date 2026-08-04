from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "snowflake_objects.json"
SETUP_DIRECTORY = ROOT / "sql" / "setup"
VERIFICATION_DIRECTORY = ROOT / "sql" / "verification"


def load_config() -> dict[str, Any]:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_snowflake_object_catalogue() -> None:
    config = load_config()

    assert config["database"] == "INDUSTRIAL_SERVICE_DB"
    assert config["schemas"] == ["RAW", "STAGING", "CORE", "ANALYTICS", "OPERATIONS"]
    assert set(config["roles"].values()) == {
        "ISP_ADMIN",
        "ISP_LOADER",
        "ISP_TRANSFORMER",
        "ISP_ANALYST",
    }
    assert config["warehouse"]["size"] == "XSMALL"
    assert config["warehouse"]["auto_suspend_seconds"] == 60


def test_setup_files_are_ordered_and_complete() -> None:
    expected = [
        "00_create_roles.sql",
        "01_create_database_warehouse.sql",
        "02_create_resource_monitor.sql",
        "03_create_schemas.sql",
        "04_grant_access.sql",
        "05_create_operations_tables.sql",
        "06_verify_configuration.sql",
    ]
    assert sorted(path.name for path in SETUP_DIRECTORY.glob("*.sql")) == expected


def test_verification_files_are_ordered_and_complete() -> None:
    expected = [
        "00_prepare_access_checks.sql",
        "01_loader_access.sql",
        "02_transformer_access.sql",
        "03_analyst_access.sql",
        "04_expected_denials.sql",
        "99_cleanup_access_checks.sql",
    ]
    assert sorted(path.name for path in VERIFICATION_DIRECTORY.glob("*.sql")) == expected


def test_sql_files_end_with_semicolons_and_have_no_tabs() -> None:
    paths = [*SETUP_DIRECTORY.glob("*.sql"), *VERIFICATION_DIRECTORY.glob("*.sql")]
    assert paths

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert text.endswith(";\n"), path
        assert "\t" not in text, path
        assert not any(line.endswith((" ", "\t")) for line in text.splitlines()), path


def test_role_boundaries_are_present() -> None:
    grant_sql = (SETUP_DIRECTORY / "04_grant_access.sql").read_text(encoding="utf-8")

    assert "ON SCHEMA INDUSTRIAL_SERVICE_DB.RAW TO ROLE ISP_LOADER" in grant_sql
    assert "ON FUTURE TABLES IN SCHEMA INDUSTRIAL_SERVICE_DB.RAW" in grant_sql
    assert "TO ROLE ISP_TRANSFORMER" in grant_sql
    assert "ON FUTURE TABLES IN SCHEMA INDUSTRIAL_SERVICE_DB.ANALYTICS" in grant_sql
    assert "TO ROLE ISP_ANALYST" in grant_sql


def test_operations_tables_are_created() -> None:
    config = load_config()
    sql = (SETUP_DIRECTORY / "05_create_operations_tables.sql").read_text(encoding="utf-8")

    for table_name in config["operations_tables"]:
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in sql
