from __future__ import annotations

from datetime import timezone
from pathlib import Path
from typing import Any

from industrial_service_platform.generation.validation import ValidationIssue
from industrial_service_platform.ingestion.connection import CursorProtocol, ParameterRow
from industrial_service_platform.ingestion.models import (
    DatasetDefinition,
    PreparedDataset,
    PreparedRecord,
    RejectedSourceRecord,
)
from industrial_service_platform.ingestion.snowflake_repository import SnowflakeRepository

UTC = timezone.utc


class FakeCursor:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection
        self.fetchone_value: tuple[Any, ...] | None = None

    def execute(self, command: str, params: ParameterRow | None = None) -> CursorProtocol:
        self.connection.executed.append((command, params))
        if command.startswith("SELECT COUNT(*)"):
            self.fetchone_value = (self.connection.new_record_count,)
        elif command.startswith("SELECT CURRENT_ROLE"):
            self.fetchone_value = (
                "ISP_LOADER",
                "INDUSTRIAL_SERVICE_WH",
                "INDUSTRIAL_SERVICE_DB",
                "RAW",
            )
        return self

    def executemany(self, command: str, seqparams: Any) -> CursorProtocol:
        self.connection.executemany_calls.append((command, list(seqparams)))
        return self

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.fetchone_value

    def fetchall(self) -> list[tuple[Any, ...]]:
        return []

    def close(self) -> None:
        return None


class FakeConnection:
    def __init__(self, new_record_count: int = 1) -> None:
        self.new_record_count = new_record_count
        self.executed: list[tuple[str, ParameterRow | None]] = []
        self.executemany_calls: list[tuple[str, list[ParameterRow]]] = []
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def close(self) -> None:
        self.closed = True


def _dataset() -> PreparedDataset:
    definition = DatasetDefinition(
        name="customers",
        source_area="ERP",
        file_name="customers.csv",
        raw_schema="RAW",
        raw_table="ERP_CUSTOMERS",
        business_key=("customer_id",),
        field_names=("customer_id", "customer_name"),
    )
    accepted = (
        PreparedRecord(
            row_number=2,
            values={"customer_id": "CUST-1", "customer_name": "One"},
            business_identifier="CUST-1",
            record_hash="hash-one",
        ),
        PreparedRecord(
            row_number=3,
            values={"customer_id": "CUST-2", "customer_name": "Two"},
            business_identifier="CUST-2",
            record_hash="hash-two",
        ),
    )
    issue = ValidationIssue(
        dataset="customers",
        row_number=4,
        field="customer_status",
        code="INVALID_ENUM_VALUE",
        message="Unsupported status.",
        business_key="CUST-3",
    )
    rejected = (
        RejectedSourceRecord(
            row_number=4,
            values={"customer_id": "CUST-3", "customer_name": "Three"},
            business_identifier="CUST-3",
            issues=(issue,),
        ),
    )
    return PreparedDataset(
        definition=definition,
        source_path=Path("customers.csv"),
        accepted=accepted,
        rejected=rejected,
    )


def test_raw_table_contains_source_and_metadata_columns() -> None:
    connection = FakeConnection()
    repository = SnowflakeRepository(connection, "INDUSTRIAL_SERVICE_DB", batch_size=1000)

    repository.ensure_raw_table(_dataset().definition)

    sql = connection.executed[0][0]
    assert "CREATE TABLE IF NOT EXISTS INDUSTRIAL_SERVICE_DB.RAW.ERP_CUSTOMERS" in sql
    assert "CUSTOMER_ID VARCHAR" in sql
    assert "_LOAD_BATCH_ID VARCHAR NOT NULL" in sql
    assert "_RECORD_HASH VARCHAR NOT NULL" in sql


def test_dataset_load_merges_new_rows_and_records_rejections() -> None:
    connection = FakeConnection(new_record_count=1)
    repository = SnowflakeRepository(connection, "INDUSTRIAL_SERVICE_DB", batch_size=1)

    result = repository.load_dataset("run-1", _dataset(), "batch-1")

    assert result.rows_received == 3
    assert result.rows_loaded == 1
    assert result.rows_skipped == 1
    assert result.rows_rejected == 1
    assert result.status == "COMPLETED_WITH_REJECTIONS_AND_SKIPS"
    merge_statements = [sql for sql, _ in connection.executed if sql.startswith("MERGE INTO")]
    assert any("INDUSTRIAL_SERVICE_DB.RAW.ERP_CUSTOMERS" in sql for sql in merge_statements)
    assert any("REJECTED_RECORDS" in sql for sql, _ in connection.executemany_calls)
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_connection_context_contains_no_account_or_user() -> None:
    connection = FakeConnection()
    repository = SnowflakeRepository(connection, "INDUSTRIAL_SERVICE_DB", batch_size=1000)

    context = repository.connection_context()

    assert context == {
        "role": "ISP_LOADER",
        "warehouse": "INDUSTRIAL_SERVICE_WH",
        "database": "INDUSTRIAL_SERVICE_DB",
        "schema": "RAW",
    }
