from __future__ import annotations

from pathlib import Path

import pytest

from industrial_service_platform.ingestion.config import (
    ConfigurationError,
    IngestionSettings,
    SnowflakeSettings,
    load_env_file,
)


def test_env_file_and_process_environment_are_combined(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "SNOWFLAKE_ACCOUNT=example-account\n"
        "SNOWFLAKE_USER=file_user\n"
        "SNOWFLAKE_AUTHENTICATOR=externalbrowser\n",
        encoding="utf-8",
    )

    settings = SnowflakeSettings.from_environment(
        env_path,
        environ={"SNOWFLAKE_USER": "process_user"},
    )

    assert settings.account == "example-account"
    assert settings.user == "process_user"
    assert settings.authenticator == "externalbrowser"
    assert settings.password is None
    assert settings.role == "ISP_LOADER"


def test_password_authentication_requires_password(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "SNOWFLAKE_ACCOUNT=example-account\n"
        "SNOWFLAKE_USER=example-user\n"
        "SNOWFLAKE_AUTHENTICATOR=snowflake\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="SNOWFLAKE_PASSWORD"):
        SnowflakeSettings.from_environment(env_path, environ={})


def test_ingestion_settings_are_validated() -> None:
    settings = IngestionSettings.from_json(Path("config/ingestion.json"))

    assert settings.source_directory == Path("data/generated")
    assert settings.source_schema_path == Path("config/source_schema.json")
    assert settings.batch_size == 1000
    assert settings.connection_attempts == 3


def test_env_parser_supports_export_and_quotes(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "export FIRST='one'\nSECOND=\"two\"\n# ignored\n",
        encoding="utf-8",
    )

    assert load_env_file(path) == {"FIRST": "one", "SECOND": "two"}
