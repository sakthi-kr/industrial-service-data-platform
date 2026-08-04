"""Configuration for local source ingestion and Snowflake connections."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigurationError(ValueError):
    """Raised when required ingestion configuration is missing or invalid."""


def load_env_file(path: Path) -> dict[str, str]:
    """Read a small KEY=VALUE environment file without shell expansion."""
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ConfigurationError(f"Invalid environment entry at {path}:{line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ConfigurationError(f"Empty environment key at {path}:{line_number}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values


def _required(values: Mapping[str, str], key: str) -> str:
    value = values.get(key, "").strip()
    if not value:
        raise ConfigurationError(f"Required setting {key} is missing")
    return value


@dataclass(frozen=True)
class SnowflakeSettings:
    """Connection settings loaded from the local environment."""

    account: str
    user: str
    authenticator: str
    password: str | None
    role: str
    warehouse: str
    database: str
    schema: str
    query_tag: str

    @classmethod
    def from_environment(
        cls,
        env_file: Path = Path(".env"),
        environ: Mapping[str, str] | None = None,
    ) -> SnowflakeSettings:
        """Load settings from .env and then override them with process variables."""
        values = load_env_file(env_file)
        process_values = os.environ if environ is None else environ
        values.update({key: value for key, value in process_values.items() if value != ""})

        authenticator = values.get("SNOWFLAKE_AUTHENTICATOR", "snowflake").strip()
        password = values.get("SNOWFLAKE_PASSWORD", "").strip() or None
        if authenticator.lower() in {"snowflake", "username_password_mfa"} and password is None:
            raise ConfigurationError(
                "SNOWFLAKE_PASSWORD is required for password-based authentication"
            )

        return cls(
            account=_required(values, "SNOWFLAKE_ACCOUNT"),
            user=_required(values, "SNOWFLAKE_USER"),
            authenticator=authenticator,
            password=password,
            role=values.get("SNOWFLAKE_ROLE", "ISP_LOADER").strip() or "ISP_LOADER",
            warehouse=(
                values.get("SNOWFLAKE_WAREHOUSE", "INDUSTRIAL_SERVICE_WH").strip()
                or "INDUSTRIAL_SERVICE_WH"
            ),
            database=(
                values.get("SNOWFLAKE_DATABASE", "INDUSTRIAL_SERVICE_DB").strip()
                or "INDUSTRIAL_SERVICE_DB"
            ),
            schema=values.get("SNOWFLAKE_SCHEMA", "RAW").strip() or "RAW",
            query_tag=(
                values.get("SNOWFLAKE_QUERY_TAG", "industrial-service-data-ingestion").strip()
                or "industrial-service-data-ingestion"
            ),
        )

    def connection_parameters(self) -> dict[str, Any]:
        """Return parameters accepted by snowflake.connector.connect."""
        parameters: dict[str, Any] = {
            "account": self.account,
            "user": self.user,
            "authenticator": self.authenticator,
            "role": self.role,
            "warehouse": self.warehouse,
            "database": self.database,
            "schema": self.schema,
            "application": "INDUSTRIAL_SERVICE_DATA_PLATFORM",
            "session_parameters": {"QUERY_TAG": self.query_tag},
            "client_session_keep_alive": False,
        }
        if self.password is not None:
            parameters["password"] = self.password
        return parameters


@dataclass(frozen=True)
class IngestionSettings:
    """Runtime settings for CSV discovery, validation, and Snowflake loading."""

    source_directory: Path
    source_schema_path: Path
    batch_size: int
    connection_attempts: int
    connection_retry_seconds: float
    local_report_directory: Path

    @classmethod
    def from_json(cls, path: Path) -> IngestionSettings:
        """Load and validate ingestion settings from JSON."""
        data = json.loads(path.read_text(encoding="utf-8"))
        settings = cls(
            source_directory=Path(str(data["source_directory"])),
            source_schema_path=Path(str(data["source_schema_path"])),
            batch_size=int(data["batch_size"]),
            connection_attempts=int(data["connection_attempts"]),
            connection_retry_seconds=float(data["connection_retry_seconds"]),
            local_report_directory=Path(str(data["local_report_directory"])),
        )
        if settings.batch_size < 1:
            raise ConfigurationError("batch_size must be at least 1")
        if settings.connection_attempts < 1:
            raise ConfigurationError("connection_attempts must be at least 1")
        if settings.connection_retry_seconds < 0:
            raise ConfigurationError("connection_retry_seconds cannot be negative")
        return settings
