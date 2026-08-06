from scripts.validate_operational_assets import main


def test_operational_static_validation_passes() -> None:
    assert main() == 0
