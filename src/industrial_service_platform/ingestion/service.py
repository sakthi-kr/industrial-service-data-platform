"""Application service coordinating local preparation and Snowflake loading."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from industrial_service_platform.ingestion.config import IngestionSettings, SnowflakeSettings
from industrial_service_platform.ingestion.connection import ConnectionProtocol, connect_with_retry
from industrial_service_platform.ingestion.models import (
    DatasetLoadResult,
    IngestionRunResult,
    PreparationResult,
)
from industrial_service_platform.ingestion.prepare import (
    load_source_catalogue,
    prepare_source_directory,
)
from industrial_service_platform.ingestion.retry import RetryPolicy
from industrial_service_platform.ingestion.snowflake_repository import SnowflakeRepository

UTC = timezone.utc
ConnectionFactory = Callable[[], ConnectionProtocol]


class IngestionService:
    """Prepare source files, connect to Snowflake, and load raw tables."""

    def __init__(
        self,
        ingestion_settings: IngestionSettings,
        snowflake_settings: SnowflakeSettings | None = None,
        connection_factory: ConnectionFactory | None = None,
    ) -> None:
        self.ingestion_settings = ingestion_settings
        self.snowflake_settings = snowflake_settings
        self._connection_factory = connection_factory

    def prepare(
        self,
        selected_datasets: tuple[str, ...] | None = None,
        source_directory: Path | None = None,
    ) -> PreparationResult:
        """Validate sources and separate accepted and rejected rows locally."""
        return prepare_source_directory(
            source_directory or self.ingestion_settings.source_directory,
            self.ingestion_settings.source_schema_path,
            selected_datasets,
        )

    def write_preparation_report(
        self,
        result: PreparationResult,
        path: Path | None = None,
    ) -> Path:
        """Write a non-sensitive local JSON summary of source preparation."""
        report_path = path or (
            self.ingestion_settings.local_report_directory / "preparation_report.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report_path

    def test_connection(self) -> dict[str, str]:
        """Open Snowflake and return the active role, warehouse, database, and schema."""
        connection = self._open_connection()
        try:
            repository = self._repository(connection)
            return repository.connection_context()
        finally:
            connection.close()

    def create_raw_tables(self, selected_datasets: tuple[str, ...] | None = None) -> int:
        """Create configured raw tables without loading source records."""
        _, definitions = load_source_catalogue(self.ingestion_settings.source_schema_path)
        if selected_datasets is None:
            selected = definitions
        else:
            selected_names = set(selected_datasets)
            unknown = selected_names - {definition.name for definition in definitions}
            if unknown:
                raise ValueError(f"Unknown datasets: {', '.join(sorted(unknown))}")
            selected = tuple(
                definition for definition in definitions if definition.name in selected_names
            )

        connection = self._open_connection()
        try:
            repository = self._repository(connection)
            for definition in selected:
                repository.ensure_raw_table(definition)
            connection.commit()
            return len(selected)
        finally:
            connection.close()

    def ingest(
        self,
        selected_datasets: tuple[str, ...] | None = None,
        source_directory: Path | None = None,
        report_path: Path | None = None,
    ) -> IngestionRunResult:
        """Prepare and idempotently load selected datasets into Snowflake."""
        preparation = self.prepare(selected_datasets, source_directory)
        self.write_preparation_report(preparation)

        run_id = str(uuid.uuid4())
        started_at = datetime.now(UTC)
        connection = self._open_connection()
        repository = self._repository(connection)
        load_results: list[DatasetLoadResult] = []

        try:
            repository.start_pipeline_run(run_id, started_at)
            for dataset in preparation.datasets:
                load_batch_id = str(uuid.uuid4())
                try:
                    result = repository.load_dataset(run_id, dataset, load_batch_id)
                except BaseException:
                    try:
                        repository.record_dataset_failure(run_id, dataset, load_batch_id)
                    except BaseException:
                        pass
                    raise
                load_results.append(result)

            finished_at = datetime.now(UTC)
            status = (
                "COMPLETED_WITH_REJECTIONS"
                if any(result.rows_rejected for result in load_results)
                else "COMPLETED"
            )
            run_result = IngestionRunResult(
                run_id=run_id,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                datasets=tuple(load_results),
            )
            repository.finish_pipeline_run(
                run_id=run_id,
                finished_at=finished_at,
                status=status,
                rows_received=run_result.rows_received,
                rows_loaded=run_result.rows_loaded,
                rows_rejected=run_result.rows_rejected,
                error_message=None,
            )
            self.write_run_report(run_result, report_path)
            return run_result
        except BaseException as error:
            finished_at = datetime.now(UTC)
            try:
                repository.finish_pipeline_run(
                    run_id=run_id,
                    finished_at=finished_at,
                    status="FAILED",
                    rows_received=preparation.rows_received,
                    rows_loaded=sum(result.rows_loaded for result in load_results),
                    rows_rejected=preparation.rows_rejected,
                    error_message=str(error)[:4000],
                )
            except BaseException:
                pass
            raise
        finally:
            connection.close()

    def write_run_report(
        self,
        result: IngestionRunResult,
        path: Path | None = None,
    ) -> Path:
        """Write the local run report used for reproducibility evidence."""
        report_path = path or (
            self.ingestion_settings.local_report_directory / f"ingestion_{result.run_id}.json"
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return report_path

    def _open_connection(self) -> ConnectionProtocol:
        if self._connection_factory is not None:
            return self._connection_factory()
        if self.snowflake_settings is None:
            raise RuntimeError("Snowflake settings are required for this operation")
        policy = RetryPolicy(
            attempts=self.ingestion_settings.connection_attempts,
            delay_seconds=self.ingestion_settings.connection_retry_seconds,
        )
        return connect_with_retry(self.snowflake_settings, policy)

    def _repository(self, connection: ConnectionProtocol) -> SnowflakeRepository:
        if self.snowflake_settings is None:
            database = "INDUSTRIAL_SERVICE_DB"
        else:
            database = self.snowflake_settings.database
        return SnowflakeRepository(
            connection=connection,
            database=database,
            batch_size=self.ingestion_settings.batch_size,
        )


def safe_connection_output(context: dict[str, str]) -> dict[str, Any]:
    """Return only non-secret session values suitable for terminal output."""
    return {
        "connected": True,
        "role": context.get("role", ""),
        "warehouse": context.get("warehouse", ""),
        "database": context.get("database", ""),
        "schema": context.get("schema", ""),
    }
