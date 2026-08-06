"""Collect a live operational snapshot from Snowflake."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from industrial_service_platform.ingestion.config import SnowflakeSettings
from industrial_service_platform.ingestion.connection import (
    ConnectionProtocol,
    connect_once,
)
from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.models import OperationalSnapshot

UTC = timezone.utc
_RELATION = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_$]*\.[A-Za-z_][A-Za-z0-9_$]*\."
    r"[A-Za-z_][A-Za-z0-9_$]*$"
)


def _relation(value: str) -> str:
    if not _RELATION.fullmatch(value):
        raise ValueError(f"Unsafe Snowflake relation: {value!r}")
    return value.upper()


def _fetch_one(
    connection: ConnectionProtocol,
    sql: str,
) -> tuple[Any, ...]:
    cursor = connection.cursor()
    try:
        cursor.execute(sql)
        row = cursor.fetchone()
    finally:
        cursor.close()
    if row is None:
        raise RuntimeError("Snowflake operational query returned no row")
    return tuple(row)


def _to_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, datetime):
        raise TypeError(f"Expected datetime from Snowflake, got {type(value).__name__}")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _to_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().casefold()
        if normalized in {"true", "yes", "on", "1"}:
            return True
        if normalized in {"false", "no", "off", "0"}:
            return False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    raise TypeError(f"Expected boolean from Snowflake, got {value!r}")


def collect_operational_snapshot(
    config: OperationalConfig,
    env_path: Path = Path(".env"),
) -> OperationalSnapshot:
    """Open an administrative project session and collect all configured checks."""
    environment = dict(os.environ)
    environment["SNOWFLAKE_ROLE"] = config.snowflake_role
    environment["SNOWFLAKE_SCHEMA"] = "OPERATIONS"
    environment["SNOWFLAKE_QUERY_TAG"] = "industrial-service-operational-health"
    settings = SnowflakeSettings.from_environment(env_path, environ=environment)
    connection = connect_once(settings)

    try:
        latest = _fetch_one(
            connection,
            """
SELECT
  RUN_ID,
  STATUS,
  FINISHED_AT,
  ROWS_RECEIVED,
  ROWS_LOADED,
  ROWS_REJECTED
FROM INDUSTRIAL_SERVICE_DB.OPERATIONS.PIPELINE_RUNS
ORDER BY STARTED_AT DESC
LIMIT 1
""".strip(),
        )

        relation_counts = {
            expectation.relation: int(
                _fetch_one(
                    connection,
                    f"SELECT COUNT(*) FROM {_relation(expectation.relation)}",
                )[0]
            )
            for expectation in config.relations
        }

        failed_quality_checks = int(
            _fetch_one(
                connection,
                """
SELECT COUNT(*)
FROM INDUSTRIAL_SERVICE_DB.OPERATIONS.DATA_QUALITY_RESULTS
WHERE UPPER(STATUS) NOT IN ('PASS', 'PASSED', 'SUCCESS')
""".strip(),
            )[0]
        )
        invalid_enrichment_rows = int(
            _fetch_one(
                connection,
                """
SELECT COUNT(*)
FROM INDUSTRIAL_SERVICE_DB.ANALYTICS.MART_TECHNICIAN_NOTE_ENRICHMENT
WHERE NOT OUTPUT_VALID
""".strip(),
            )[0]
        )

        escaped_warehouse = config.warehouse_name.replace("'", "''")
        cursor = connection.cursor()
        try:
            cursor.execute(f"SHOW WAREHOUSES LIKE '{escaped_warehouse}'")
            cursor.execute(
                """
SELECT "size", "auto_suspend", "auto_resume"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
""".strip()
            )
            warehouse = cursor.fetchone()
        finally:
            cursor.close()
        if warehouse is None:
            raise RuntimeError(
                f"Warehouse {config.warehouse_name} was not returned by SHOW WAREHOUSES"
            )

        return OperationalSnapshot(
            observed_at=datetime.now(UTC),
            latest_run_id=str(latest[0]),
            latest_run_status=str(latest[1]),
            latest_run_finished_at=_to_datetime(latest[2]),
            latest_rows_received=int(latest[3]),
            latest_rows_loaded=int(latest[4]),
            latest_rows_rejected=int(latest[5]),
            relation_counts=relation_counts,
            failed_quality_checks=failed_quality_checks,
            invalid_enrichment_rows=invalid_enrichment_rows,
            warehouse_size=str(warehouse[0]),
            warehouse_auto_suspend_seconds=int(warehouse[1]),
            warehouse_auto_resume=_to_bool(warehouse[2]),
        )
    finally:
        connection.close()
