"""Small retry helper used for recoverable connection failures."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Fixed-delay retry settings."""

    attempts: int
    delay_seconds: float


def run_with_retry(
    operation: Callable[[], T],
    policy: RetryPolicy,
    retriable_exceptions: tuple[type[BaseException], ...],
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Run an operation until it succeeds or the retry budget is exhausted."""
    if policy.attempts < 1:
        raise ValueError("Retry attempts must be at least 1")

    last_error: BaseException | None = None
    for attempt in range(1, policy.attempts + 1):
        try:
            return operation()
        except retriable_exceptions as error:
            last_error = error
            if attempt == policy.attempts:
                raise
            sleep(policy.delay_seconds)

    if last_error is not None:
        raise last_error
    raise RuntimeError("Retry loop ended without a result or exception")
