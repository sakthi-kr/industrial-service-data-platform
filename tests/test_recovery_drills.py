from pathlib import Path

from industrial_service_platform.operations.config import OperationalConfig
from industrial_service_platform.operations.drills import run_recovery_drills


def test_all_recovery_drills_detect_the_expected_failure() -> None:
    config = OperationalConfig.from_json(Path("config/operational_health.json"))
    results = run_recovery_drills(config)

    assert len(results) == 6
    assert all(result.detected for result in results)
    assert all(result.overall_status == "FAIL" for result in results)
