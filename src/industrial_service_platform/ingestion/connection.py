"""Snowflake connector boundary kept small for testing and type checking."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol, cast

from industrial_service_platform.ingestion.config import SnowflakeSettings
from industrial_service_platform.ingestion.retry import RetryPolicy, run_with_retry

ParameterRow = Sequence[Any] | Mapping[str, Any]


class CursorProtocol(Protocol):
    """Subset of the Snowflake cursor API used by the project."""

    def execute(self, command: str, params: ParameterRow | None = None) -> CursorProtocol: ...

    def executemany(self, command: str, seqparams: Iterable[ParameterRow]) -> CursorProtocol: ...

    def fetchone(self) -> Sequence[Any] | None: ...

    def fetchall(self) -> list[Sequence[Any]]: ...

    def close(self) -> None: ...


class ConnectionProtocol(Protocol):
    """Subset of the Snowflake connection API used by the project."""

    def cursor(self) -> CursorProtocol: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def close(self) -> None: ...


def connect_once(settings: SnowflakeSettings) -> ConnectionProtocol:
    """Open one Snowflake connector connection."""
    import snowflake.connector

    connection = snowflake.connector.connect(**settings.connection_parameters())
    return cast(ConnectionProtocol, connection)


def connect_with_retry(
    settings: SnowflakeSettings,
    policy: RetryPolicy,
) -> ConnectionProtocol:
    """Retry recoverable connector connection failures."""
    import snowflake.connector.errors

    retriable = (
        snowflake.connector.errors.OperationalError,
        snowflake.connector.errors.InterfaceError,
    )
    return run_with_retry(lambda: connect_once(settings), policy, retriable)
