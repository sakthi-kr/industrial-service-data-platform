"""Data structures shared by ingestion preparation and Snowflake loading."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from industrial_service_platform.generation.validation import Row, ValidationIssue


@dataclass(frozen=True)
class DatasetDefinition:
    """One source dataset and its configured Snowflake raw target."""

    name: str
    source_area: str
    file_name: str
    raw_schema: str
    raw_table: str
    business_key: tuple[str, ...]
    field_names: tuple[str, ...]

    @property
    def qualified_raw_table(self) -> str:
        return f"{self.raw_schema}.{self.raw_table}"


@dataclass(frozen=True)
class PreparedRecord:
    """A validated source record ready for loading."""

    row_number: int
    values: Row
    business_identifier: str
    record_hash: str


@dataclass(frozen=True)
class RejectedSourceRecord:
    """A source row rejected by one or more validation checks."""

    row_number: int
    values: Row
    business_identifier: str
    issues: tuple[ValidationIssue, ...]


@dataclass(frozen=True)
class PreparedDataset:
    """Accepted and rejected records for one source file."""

    definition: DatasetDefinition
    source_path: Path
    accepted: tuple[PreparedRecord, ...]
    rejected: tuple[RejectedSourceRecord, ...]

    @property
    def rows_received(self) -> int:
        return len(self.accepted) + len(self.rejected)


@dataclass(frozen=True)
class PreparationResult:
    """Complete local preparation result before a Snowflake connection is opened."""

    source_directory: Path
    datasets: tuple[PreparedDataset, ...]
    prepared_at: datetime

    @property
    def rows_received(self) -> int:
        return sum(dataset.rows_received for dataset in self.datasets)

    @property
    def rows_accepted(self) -> int:
        return sum(len(dataset.accepted) for dataset in self.datasets)

    @property
    def rows_rejected(self) -> int:
        return sum(len(dataset.rejected) for dataset in self.datasets)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_directory": str(self.source_directory),
            "prepared_at": self.prepared_at.isoformat(),
            "rows_received": self.rows_received,
            "rows_accepted": self.rows_accepted,
            "rows_rejected": self.rows_rejected,
            "datasets": [
                {
                    "dataset": dataset.definition.name,
                    "source_file": dataset.definition.file_name,
                    "raw_table": dataset.definition.qualified_raw_table,
                    "rows_received": dataset.rows_received,
                    "rows_accepted": len(dataset.accepted),
                    "rows_rejected": len(dataset.rejected),
                }
                for dataset in self.datasets
            ],
        }


@dataclass(frozen=True)
class DatasetLoadResult:
    """Snowflake load result for one prepared dataset."""

    dataset: str
    source_file: str
    raw_table: str
    rows_received: int
    rows_loaded: int
    rows_rejected: int
    rows_skipped: int
    status: str


@dataclass(frozen=True)
class IngestionRunResult:
    """Summary of one complete ingestion execution."""

    run_id: str
    status: str
    started_at: datetime
    finished_at: datetime
    datasets: tuple[DatasetLoadResult, ...]

    @property
    def rows_received(self) -> int:
        return sum(result.rows_received for result in self.datasets)

    @property
    def rows_loaded(self) -> int:
        return sum(result.rows_loaded for result in self.datasets)

    @property
    def rows_rejected(self) -> int:
        return sum(result.rows_rejected for result in self.datasets)

    @property
    def rows_skipped(self) -> int:
        return sum(result.rows_skipped for result in self.datasets)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "rows_received": self.rows_received,
            "rows_loaded": self.rows_loaded,
            "rows_rejected": self.rows_rejected,
            "rows_skipped": self.rows_skipped,
            "datasets": [asdict(result) for result in self.datasets],
        }
