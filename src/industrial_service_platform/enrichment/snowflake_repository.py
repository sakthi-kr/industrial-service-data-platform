"""Publish evaluated note-enrichment outputs to Snowflake."""

from __future__ import annotations

import csv
import os
import uuid
from pathlib import Path
from typing import Any

from industrial_service_platform.enrichment.config import EnrichmentConfig
from industrial_service_platform.ingestion.config import SnowflakeSettings
from industrial_service_platform.ingestion.connection import ConnectionProtocol, connect_once

COLUMNS = (
    "NOTE_ID",
    "MODEL_VERSION",
    "PREDICTED_FAULT_CATEGORY",
    "PREDICTED_PRIORITY",
    "PREDICTED_COMPONENT",
    "RECOMMENDED_TEAM",
    "GENERATED_SUMMARY",
    "FAULT_CONFIDENCE",
    "PRIORITY_CONFIDENCE",
    "OUTPUT_VALID",
    "PROCESSED_AT",
)


def read_prediction_rows(path: Path) -> list[tuple[Any, ...]]:
    """Read the locally evaluated prediction CSV."""
    if not path.is_file():
        raise FileNotFoundError(f"Prediction file is missing: {path}")
    rows: list[tuple[Any, ...]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                (
                    row["note_id"],
                    row["model_version"],
                    row["predicted_fault_category"],
                    row["predicted_priority"],
                    row["predicted_component"],
                    row["recommended_team"],
                    row["generated_summary"],
                    float(row["fault_confidence"]),
                    float(row["priority_confidence"]),
                    row["output_valid"].lower() == "true",
                    row["processed_at"],
                )
            )
    if not rows:
        raise ValueError("Prediction file contains no rows")
    return rows


def snowflake_settings(config: EnrichmentConfig, env_file: Path) -> SnowflakeSettings:
    """Load the existing private connection and select the transformer role."""
    environment = dict(os.environ)
    environment.update(
        {
            "SNOWFLAKE_ROLE": config.snowflake_role,
            "SNOWFLAKE_DATABASE": config.snowflake_database,
            "SNOWFLAKE_SCHEMA": config.snowflake_schema,
            "SNOWFLAKE_QUERY_TAG": "industrial-service-note-enrichment",
        }
    )
    return SnowflakeSettings.from_environment(env_file, environ=environment)


class EnrichmentRepository:
    """Small Snowflake boundary for idempotent prediction publication."""

    def __init__(self, connection: ConnectionProtocol, config: EnrichmentConfig) -> None:
        self.connection = connection
        self.config = config

    @property
    def target(self) -> str:
        return (
            f"{self.config.snowflake_database}."
            f"{self.config.snowflake_schema}."
            f"{self.config.snowflake_table}"
        )

    def publish(self, rows: list[tuple[Any, ...]]) -> dict[str, Any]:
        """Merge one model version without creating duplicate note rows."""
        cursor = self.connection.cursor()
        temp_table = f"TEMP_NOTE_ENRICHMENT_{uuid.uuid4().hex.upper()}"
        try:
            cursor.execute(
                f"""
                create table if not exists {self.target} (
                  NOTE_ID varchar not null,
                  MODEL_VERSION varchar not null,
                  PREDICTED_FAULT_CATEGORY varchar not null,
                  PREDICTED_PRIORITY varchar not null,
                  PREDICTED_COMPONENT varchar not null,
                  RECOMMENDED_TEAM varchar not null,
                  GENERATED_SUMMARY varchar not null,
                  FAULT_CONFIDENCE number(18, 6) not null,
                  PRIORITY_CONFIDENCE number(18, 6) not null,
                  OUTPUT_VALID boolean not null,
                  PROCESSED_AT timestamp_tz not null,
                  constraint UQ_NOTE_ENRICHMENT unique (NOTE_ID, MODEL_VERSION)
                )
                """
            )
            cursor.execute(f"create temporary table {temp_table} like {self.target}")
            placeholders = ", ".join(["%s"] * len(COLUMNS))
            insert_sql = f"insert into {temp_table} ({', '.join(COLUMNS)}) values ({placeholders})"
            for start in range(0, len(rows), self.config.batch_size):
                cursor.executemany(
                    insert_sql,
                    rows[start : start + self.config.batch_size],
                )
            update_assignments = ", ".join(
                f"target.{column} = source.{column}"
                for column in COLUMNS
                if column not in {"NOTE_ID", "MODEL_VERSION"}
            )
            cursor.execute(
                f"""
                merge into {self.target} as target
                using {temp_table} as source
                  on target.NOTE_ID = source.NOTE_ID
                 and target.MODEL_VERSION = source.MODEL_VERSION
                when matched then update set {update_assignments}
                when not matched then insert ({", ".join(COLUMNS)})
                values ({", ".join(f"source.{column}" for column in COLUMNS)})
                """
            )
            model_version = str(rows[0][1])
            cursor.execute(
                f"select count(*) from {self.target} where MODEL_VERSION = %s",
                (model_version,),
            )
            result = cursor.fetchone()
            stored_rows = int(result[0]) if result is not None else 0
            self.connection.commit()
            return {
                "input_rows": len(rows),
                "stored_rows": stored_rows,
                "model_version": model_version,
                "target": self.target,
                "status": "COMPLETED",
            }
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()


def publish_predictions(
    config: EnrichmentConfig,
    *,
    env_file: Path = Path(".env"),
) -> dict[str, Any]:
    """Connect, publish predictions, and close the session safely."""
    rows = read_prediction_rows(config.predictions_path)
    settings = snowflake_settings(config, env_file)
    connection = connect_once(settings)
    try:
        return EnrichmentRepository(connection, config).publish(rows)
    finally:
        connection.close()
