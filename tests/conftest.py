from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def small_generation_config(tmp_path: Path) -> Path:
    config: dict[str, Any] = {
        "seed": 20260803,
        "history_start": "2024-01-01T00:00:00Z",
        "reporting_as_of": "2026-08-01T00:00:00Z",
        "output_directory": str(tmp_path / "generated"),
        "sample_directory": str(tmp_path / "samples"),
        "sample_rows_per_dataset": 5,
        "row_counts": {
            "assets": 30,
            "customer_cases": 80,
            "customers": 8,
            "equipment_alerts": 150,
            "parts": 20,
            "service_contracts": 16,
            "service_order_parts": 120,
            "service_orders": 60,
            "sites": 12,
            "technician_notes": 50,
            "technicians": 10,
        },
    }
    path = tmp_path / "data_generation.json"
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path
