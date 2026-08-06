from pathlib import Path
from typing import Any

from industrial_service_platform.enrichment.config import EnrichmentConfig
from industrial_service_platform.enrichment.snowflake_repository import EnrichmentRepository


class FakeCursor:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.batch_rows: list[tuple[Any, ...]] = []

    def execute(self, command: str, params: Any = None) -> "FakeCursor":
        self.commands.append(command)
        return self

    def executemany(self, command: str, seqparams: Any) -> "FakeCursor":
        self.commands.append(command)
        self.batch_rows = list(seqparams)
        return self

    def fetchone(self) -> tuple[int]:
        return (len(self.batch_rows),)

    def fetchall(self) -> list[tuple[Any, ...]]:
        return []

    def close(self) -> None:
        return None


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_value = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self) -> FakeCursor:
        return self.cursor_value

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        return None


def test_repository_uses_idempotent_merge() -> None:
    config = EnrichmentConfig.from_json(Path("config/note_enrichment.json"))
    connection = FakeConnection()
    row = (
        "NOTE-1",
        "tfidf-logreg-v1",
        "VIBRATION",
        "HIGH",
        "rotor and bearing assembly",
        "RELIABILITY_ENGINEERING",
        "Summary",
        0.9,
        0.8,
        True,
        "2026-08-06T00:00:00+00:00",
    )
    result = EnrichmentRepository(connection, config).publish([row])
    sql = "\n".join(connection.cursor_value.commands).lower()
    assert "merge into" in sql
    assert "note_id = source.note_id" in sql
    assert "model_version = source.model_version" in sql
    assert connection.committed
    assert not connection.rolled_back
    assert result["stored_rows"] == 1
