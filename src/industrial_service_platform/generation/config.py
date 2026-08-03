"""Configuration loading for deterministic synthetic-data generation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc


def parse_utc_timestamp(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and normalise it to UTC."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"Timestamp must include a timezone: {value}")
    return parsed.astimezone(UTC)


@dataclass(frozen=True)
class GenerationConfig:
    """Validated settings used by the synthetic-data generator."""

    seed: int
    history_start: datetime
    reporting_as_of: datetime
    output_directory: Path
    sample_directory: Path
    sample_rows_per_dataset: int
    row_counts: dict[str, int]

    @classmethod
    def from_json(cls, path: Path) -> GenerationConfig:
        """Load and validate a generation configuration file."""
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Generation configuration must contain a JSON object")

        required_keys = {
            "seed",
            "history_start",
            "reporting_as_of",
            "output_directory",
            "sample_directory",
            "sample_rows_per_dataset",
            "row_counts",
        }
        missing = sorted(required_keys - raw.keys())
        if missing:
            raise ValueError(f"Missing generation configuration keys: {missing}")

        row_counts_raw = raw["row_counts"]
        if not isinstance(row_counts_raw, dict):
            raise ValueError("row_counts must be a JSON object")

        row_counts: dict[str, int] = {}
        for dataset, value in row_counts_raw.items():
            if not isinstance(dataset, str) or not isinstance(value, int):
                raise ValueError("row_counts must map dataset names to integers")
            if value <= 0:
                raise ValueError(f"Row count must be positive for {dataset}")
            row_counts[dataset] = value

        history_start = parse_utc_timestamp(_require_string(raw, "history_start"))
        reporting_as_of = parse_utc_timestamp(_require_string(raw, "reporting_as_of"))
        if history_start >= reporting_as_of:
            raise ValueError("history_start must be earlier than reporting_as_of")

        sample_rows = raw["sample_rows_per_dataset"]
        if not isinstance(sample_rows, int) or sample_rows <= 0:
            raise ValueError("sample_rows_per_dataset must be a positive integer")

        seed = raw["seed"]
        if not isinstance(seed, int):
            raise ValueError("seed must be an integer")

        return cls(
            seed=seed,
            history_start=history_start,
            reporting_as_of=reporting_as_of,
            output_directory=Path(_require_string(raw, "output_directory")),
            sample_directory=Path(_require_string(raw, "sample_directory")),
            sample_rows_per_dataset=sample_rows,
            row_counts=row_counts,
        )

    def required_count(self, dataset: str) -> int:
        """Return an explicitly configured row count."""
        try:
            return self.row_counts[dataset]
        except KeyError as exc:
            raise ValueError(f"Missing row count for required dataset: {dataset}") from exc

    def as_manifest_dict(self) -> dict[str, Any]:
        """Return stable JSON-compatible configuration content."""
        return {
            "seed": self.seed,
            "history_start": _format_utc(self.history_start),
            "reporting_as_of": _format_utc(self.reporting_as_of),
            "sample_rows_per_dataset": self.sample_rows_per_dataset,
            "row_counts": dict(sorted(self.row_counts.items())),
        }


def _require_string(raw: dict[str, Any], key: str) -> str:
    value = raw[key]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
