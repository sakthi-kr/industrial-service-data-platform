from scripts.validate_analytics_assets import main


def test_analytics_asset_validation_passes() -> None:
    assert main() == 0
