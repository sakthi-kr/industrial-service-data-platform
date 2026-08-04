"""Snowflake SQL operations for idempotent raw loading and audit records."""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from typing import Any

from industrial_service_platform.ingestion.connection import ConnectionProtocol
from industrial_service_platform.ingestion.models import (
    DatasetDefinition,
    DatasetLoadResult,
    PreparedDataset,
)

UTC = timezone.utc
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")


class SnowflakeRepositoryError(RuntimeError):
    """Raised when a Snowflake result is missing or internally inconsistent."""


def _identifier(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"Unsafe Snowflake identifier: {value!r}")
    return value.upper()


def _chunks(rows: Sequence[tuple[Any, ...]], size: int) -> Iterable[Sequence[tuple[Any, ...]]]:
    for start in range(0, len(rows), size):
        yield rows[start : start + size]


class SnowflakeRepository:
    """Execute the project ingestion contract against one Snowflake connection."""

    def __init__(self, connection: ConnectionProtocol, database: str, batch_size: int) -> None:
        self.connection = connection
        self.database = _identifier(database)
        self.batch_size = batch_size

    def _qualified(self, schema: str, table: str) -> str:
        return f"{self.database}.{_identifier(schema)}.{_identifier(table)}"

    def _execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
        finally:
            cursor.close()

    def _fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> Sequence[Any]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        finally:
            cursor.close()
        if row is None:
            raise SnowflakeRepositoryError("Snowflake query returned no row")
        return row

    def connection_context(self) -> dict[str, str]:
        """Return the active non-secret Snowflake session context."""
        row = self._fetch_one(
            "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
        )
        labels = ("role", "warehouse", "database", "schema")
        return {
            label: "" if value is None else str(value)
            for label, value in zip(labels, row, strict=True)
        }

    def ensure_raw_table(self, definition: DatasetDefinition) -> None:
        """Create a raw table whose source fields remain text for downstream casting."""
        source_columns = [f"  {_identifier(name)} VARCHAR" for name in definition.field_names]
        metadata_columns = [
            "  _LOAD_BATCH_ID VARCHAR NOT NULL",
            "  _SOURCE_SYSTEM VARCHAR NOT NULL",
            "  _SOURCE_FILE_NAME VARCHAR NOT NULL",
            "  _SOURCE_ROW_NUMBER NUMBER(38, 0) NOT NULL",
            "  _INGESTED_AT TIMESTAMP_TZ NOT NULL",
            "  _RECORD_HASH VARCHAR NOT NULL",
        ]
        columns = ",\n".join([*source_columns, *metadata_columns])
        target = self._qualified(definition.raw_schema, definition.raw_table)
        self._execute(f"CREATE TABLE IF NOT EXISTS {target} (\n{columns}\n)")

    def start_pipeline_run(self, run_id: str, started_at: datetime) -> None:
        """Record a pipeline run before any dataset is loaded."""
        table = self._qualified("OPERATIONS", "PIPELINE_RUNS")
        self._execute(
            f"""
INSERT INTO {table} (
  RUN_ID, SOURCE_NAME, STARTED_AT, STATUS,
  ROWS_RECEIVED, ROWS_LOADED, ROWS_REJECTED
)
VALUES (%s, %s, %s, %s, 0, 0, 0)
""".strip(),
            (run_id, "CSV_FILES", started_at, "RUNNING"),
        )
        self.connection.commit()

    def finish_pipeline_run(
        self,
        run_id: str,
        finished_at: datetime,
        status: str,
        rows_received: int,
        rows_loaded: int,
        rows_rejected: int,
        error_message: str | None,
    ) -> None:
        """Finalize the run-level audit record."""
        table = self._qualified("OPERATIONS", "PIPELINE_RUNS")
        self._execute(
            f"""
UPDATE {table}
SET FINISHED_AT = %s,
    STATUS = %s,
    ROWS_RECEIVED = %s,
    ROWS_LOADED = %s,
    ROWS_REJECTED = %s,
    ERROR_MESSAGE = %s
WHERE RUN_ID = %s
""".strip(),
            (
                finished_at,
                status,
                rows_received,
                rows_loaded,
                rows_rejected,
                error_message,
                run_id,
            ),
        )
        self.connection.commit()

    def record_dataset_failure(
        self,
        run_id: str,
        dataset: PreparedDataset,
        load_batch_id: str,
    ) -> None:
        """Write a failed dataset result after its transaction has rolled back."""
        table = self._qualified("OPERATIONS", "INGESTION_RESULTS")
        self._execute(
            f"""
INSERT INTO {table} (
  RESULT_ID, RUN_ID, DATASET_NAME, SOURCE_FILE_NAME, LOAD_BATCH_ID,
  ROWS_RECEIVED, ROWS_LOADED, ROWS_REJECTED, STATUS
)
VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s)
""".strip(),
            (
                str(uuid.uuid4()),
                run_id,
                dataset.definition.name,
                dataset.definition.file_name,
                load_batch_id,
                dataset.rows_received,
                len(dataset.rejected),
                "FAILED",
            ),
        )
        self.connection.commit()

    def load_dataset(
        self,
        run_id: str,
        dataset: PreparedDataset,
        load_batch_id: str,
    ) -> DatasetLoadResult:
        """Load one prepared dataset with a hash-based idempotent merge."""
        definition = dataset.definition
        self.ensure_raw_table(definition)

        target = self._qualified(definition.raw_schema, definition.raw_table)
        temporary_name = _identifier(f"TMP_{definition.raw_table}_{uuid.uuid4().hex[:10]}")
        temporary = self._qualified(definition.raw_schema, temporary_name)
        self._execute(f"CREATE TEMPORARY TABLE {temporary} LIKE {target}")

        try:
            self._execute("BEGIN")
            self._insert_prepared_records(temporary, dataset, load_batch_id)
            rows_loaded = self._count_new_records(temporary, target)
            self._merge_new_records(temporary, target, definition)
            self._insert_rejected_records(run_id, dataset, load_batch_id)

            rows_skipped = len(dataset.accepted) - rows_loaded
            status = self._dataset_status(len(dataset.rejected), rows_skipped)
            self._insert_ingestion_result(
                run_id=run_id,
                dataset=dataset,
                load_batch_id=load_batch_id,
                rows_loaded=rows_loaded,
                status=status,
            )
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise
        finally:
            try:
                self._execute(f"DROP TABLE IF EXISTS {temporary}")
            except BaseException:
                pass

        return DatasetLoadResult(
            dataset=definition.name,
            source_file=definition.file_name,
            raw_table=definition.qualified_raw_table,
            rows_received=dataset.rows_received,
            rows_loaded=rows_loaded,
            rows_rejected=len(dataset.rejected),
            rows_skipped=rows_skipped,
            status=status,
        )

    def _insert_prepared_records(
        self,
        temporary: str,
        dataset: PreparedDataset,
        load_batch_id: str,
    ) -> None:
        if not dataset.accepted:
            return

        definition = dataset.definition
        source_columns = [_identifier(name) for name in definition.field_names]
        metadata_columns = [
            "_LOAD_BATCH_ID",
            "_SOURCE_SYSTEM",
            "_SOURCE_FILE_NAME",
            "_SOURCE_ROW_NUMBER",
            "_INGESTED_AT",
            "_RECORD_HASH",
        ]
        columns = [*source_columns, *metadata_columns]
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"INSERT INTO {temporary} ({', '.join(columns)}) VALUES ({placeholders})"
        ingested_at = datetime.now(UTC)
        parameter_rows = [
            (
                *[record.values.get(name, "") for name in definition.field_names],
                load_batch_id,
                definition.source_area,
                definition.file_name,
                record.row_number,
                ingested_at,
                record.record_hash,
            )
            for record in dataset.accepted
        ]

        cursor = self.connection.cursor()
        try:
            for batch in _chunks(parameter_rows, self.batch_size):
                cursor.executemany(sql, batch)
        finally:
            cursor.close()

    def _count_new_records(self, temporary: str, target: str) -> int:
        row = self._fetch_one(
            f"""
SELECT COUNT(*)
FROM {temporary} AS source
LEFT JOIN {target} AS target
  ON target._RECORD_HASH = source._RECORD_HASH
WHERE target._RECORD_HASH IS NULL
""".strip()
        )
        return int(row[0])

    def _merge_new_records(
        self,
        temporary: str,
        target: str,
        definition: DatasetDefinition,
    ) -> None:
        columns = [
            *[_identifier(name) for name in definition.field_names],
            "_LOAD_BATCH_ID",
            "_SOURCE_SYSTEM",
            "_SOURCE_FILE_NAME",
            "_SOURCE_ROW_NUMBER",
            "_INGESTED_AT",
            "_RECORD_HASH",
        ]
        insert_columns = ", ".join(columns)
        source_values = ", ".join(f"source.{column}" for column in columns)
        self._execute(
            f"""
MERGE INTO {target} AS target
USING {temporary} AS source
  ON target._RECORD_HASH = source._RECORD_HASH
WHEN NOT MATCHED THEN
  INSERT ({insert_columns})
  VALUES ({source_values})
""".strip()
        )

    def _insert_rejected_records(
        self,
        run_id: str,
        dataset: PreparedDataset,
        load_batch_id: str,
    ) -> None:
        if not dataset.rejected:
            return

        table = self._qualified("OPERATIONS", "REJECTED_RECORDS")
        sql = f"""
INSERT INTO {table} (
  REJECTION_ID, RUN_ID, LOAD_BATCH_ID, SOURCE_SYSTEM, SOURCE_FILE_NAME,
  SOURCE_ROW_NUMBER, BUSINESS_IDENTIFIER, REJECTION_CODE,
  REJECTION_MESSAGE, RAW_RECORD_PAYLOAD
)
SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, PARSE_JSON(%s)
""".strip()
        parameter_rows: list[tuple[Any, ...]] = []
        for rejected in dataset.rejected:
            payload = json.dumps(rejected.values, ensure_ascii=False, sort_keys=True)
            for issue in rejected.issues:
                parameter_rows.append(
                    (
                        str(uuid.uuid4()),
                        run_id,
                        load_batch_id,
                        dataset.definition.source_area,
                        dataset.definition.file_name,
                        rejected.row_number,
                        rejected.business_identifier or None,
                        issue.code,
                        issue.message,
                        payload,
                    )
                )

        cursor = self.connection.cursor()
        try:
            for batch in _chunks(parameter_rows, self.batch_size):
                cursor.executemany(sql, batch)
        finally:
            cursor.close()

    def _insert_ingestion_result(
        self,
        run_id: str,
        dataset: PreparedDataset,
        load_batch_id: str,
        rows_loaded: int,
        status: str,
    ) -> None:
        table = self._qualified("OPERATIONS", "INGESTION_RESULTS")
        self._execute(
            f"""
INSERT INTO {table} (
  RESULT_ID, RUN_ID, DATASET_NAME, SOURCE_FILE_NAME, LOAD_BATCH_ID,
  ROWS_RECEIVED, ROWS_LOADED, ROWS_REJECTED, STATUS
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""".strip(),
            (
                str(uuid.uuid4()),
                run_id,
                dataset.definition.name,
                dataset.definition.file_name,
                load_batch_id,
                dataset.rows_received,
                rows_loaded,
                len(dataset.rejected),
                status,
            ),
        )

    @staticmethod
    def _dataset_status(rows_rejected: int, rows_skipped: int) -> str:
        if rows_rejected and rows_skipped:
            return "COMPLETED_WITH_REJECTIONS_AND_SKIPS"
        if rows_rejected:
            return "COMPLETED_WITH_REJECTIONS"
        if rows_skipped:
            return "COMPLETED_WITH_SKIPS"
        return "COMPLETED"
