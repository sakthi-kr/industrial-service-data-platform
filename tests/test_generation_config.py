from __future__ import annotations

import json
from pathlib import Path

import pytest

from industrial_service_platform.generation.config import GenerationConfig


def test_generation_config_loads_valid_json(small_generation_config: Path) -> None:
    config = GenerationConfig.from_json(small_generation_config)

    assert config.seed == 20260803
    assert config.required_count("assets") == 30
    assert config.sample_rows_per_dataset == 5
    assert config.history_start < config.reporting_as_of


def test_generation_config_rejects_non_positive_counts(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps(
            {
                "seed": 1,
                "history_start": "2024-01-01T00:00:00Z",
                "reporting_as_of": "2026-01-01T00:00:00Z",
                "output_directory": "data/generated",
                "sample_directory": "data/samples",
                "sample_rows_per_dataset": 5,
                "row_counts": {"assets": 0},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Row count must be positive"):
        GenerationConfig.from_json(path)
