"""Validate the Snowflake object catalogue and SQL setup files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "snowflake_objects.json"
SETUP_DIRECTORY = ROOT / "sql" / "setup"
VERIFICATION_DIRECTORY = ROOT / "sql" / "verification"

EXPECTED_SETUP_FILES = [
    "00_create_roles.sql",
    "01_create_database_warehouse.sql",
    "02_create_resource_monitor.sql",
    "03_create_schemas.sql",
    "04_grant_access.sql",
    "05_create_operations_tables.sql",
    "06_verify_configuration.sql",
]

EXPECTED_VERIFICATION_FILES = [
    "00_prepare_access_checks.sql",
    "01_loader_access.sql",
    "02_transformer_access.sql",
    "03_analyst_access.sql",
    "04_expected_denials.sql",
    "99_cleanup_access_checks.sql",
]


def load_config() -> dict[str, Any]:
    """Load the Snowflake object catalogue."""
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Snowflake configuration must contain a JSON object")
    return raw


def split_statements(text: str) -> list[str]:
    """Split simple Snowflake setup SQL into semicolon-terminated statements."""
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False

    for character in text:
        if character == "'":
            in_single_quote = not in_single_quote
        current.append(character)
        if character == ";" and not in_single_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    remainder = "".join(current).strip()
    if remainder:
        raise ValueError("SQL file contains a statement without a trailing semicolon")
    return statements


def validate() -> list[str]:
    """Return validation errors for the Snowflake infrastructure files."""
    errors: list[str] = []
    config = load_config()

    expected_keys = {
        "database",
        "warehouse",
        "resource_monitor",
        "schemas",
        "roles",
        "operations_tables",
    }
    missing_keys = sorted(expected_keys - config.keys())
    if missing_keys:
        errors.append(f"Missing configuration keys: {missing_keys}")

    setup_names = sorted(path.name for path in SETUP_DIRECTORY.glob("*.sql"))
    if setup_names != EXPECTED_SETUP_FILES:
        errors.append(f"Unexpected setup files: {setup_names}")

    verification_names = sorted(path.name for path in VERIFICATION_DIRECTORY.glob("*.sql"))
    if verification_names != EXPECTED_VERIFICATION_FILES:
        errors.append(f"Unexpected verification files: {verification_names}")

    combined_setup = "\n".join(
        (SETUP_DIRECTORY / name).read_text(encoding="utf-8") for name in EXPECTED_SETUP_FILES
    )

    required_tokens = [
        config["database"],
        config["warehouse"]["name"],
        config["resource_monitor"]["name"],
        *config["schemas"],
        *config["roles"].values(),
        *config["operations_tables"],
    ]
    for token in required_tokens:
        if token not in combined_setup:
            errors.append(f"Missing SQL token: {token}")

    sql_paths = [*SETUP_DIRECTORY.glob("*.sql"), *VERIFICATION_DIRECTORY.glob("*.sql")]
    for sql_path in sql_paths:
        text = sql_path.read_text(encoding="utf-8")
        if "\t" in text:
            errors.append(f"Tab character found in {sql_path.relative_to(ROOT)}")
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            errors.append(f"Trailing whitespace found in {sql_path.relative_to(ROOT)}")
        try:
            split_statements(text)
        except ValueError as exc:
            errors.append(f"{sql_path.relative_to(ROOT)}: {exc}")

    grant_sql = (SETUP_DIRECTORY / "04_grant_access.sql").read_text(encoding="utf-8")
    future_grant_count = len(re.findall(r"ON FUTURE (?:TABLES|VIEWS)", grant_sql))
    if future_grant_count < 8:
        errors.append("Expected at least eight future table or view grants")

    return errors


def main() -> int:
    """Run the Snowflake static validation command."""
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    config = load_config()
    print(
        "Snowflake setup validation passed: "
        f"{len(config['schemas'])} schemas, "
        f"{len(config['roles'])} roles, "
        f"{len(config['operations_tables'])} operations tables"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
