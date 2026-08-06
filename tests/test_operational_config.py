import json
from pathlib import Path

import pytest

from industrial_service_platform.operations.config import (
    OperationalConfig,
    OperationalConfigurationError,
)


def test_operational_config_loads_expected_relations() -> None:
    config = OperationalConfig.from_json(Path("config/operational_health.json"))

    assert config.snowflake_role == "ISP_ADMIN"
    assert config.max_pipeline_age_hours == pytest.approx(96.0)
    assert len(config.relations) == 17
    assert sum(item.expected_rows for item in config.relations) == 113875


def test_operational_config_rejects_duplicate_relations(tmp_path: Path) -> None:
    source = json.loads(Path("config/operational_health.json").read_text(encoding="utf-8"))
    source["relations"].append(source["relations"][0])
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(source), encoding="utf-8")

    with pytest.raises(
        OperationalConfigurationError,
        match="must be unique",
    ):
        OperationalConfig.from_json(path)
