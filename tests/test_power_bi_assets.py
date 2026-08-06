import json
from pathlib import Path

from scripts.validate_power_bi_assets import EXPECTED_MEASURES, main, measure_names


def test_power_bi_static_validation_passes() -> None:
    assert main() == 0


def test_power_bi_theme_has_expected_palette() -> None:
    theme = json.loads(
        Path("dashboards/power_bi/industrial_service_theme.json").read_text(encoding="utf-8")
    )
    assert theme["name"] == "Industrial Service Operations"
    assert len(theme["dataColors"]) == 8


def test_dax_measure_set_is_complete() -> None:
    text = Path("dashboards/power_bi/dax_measures.dax").read_text(encoding="utf-8")
    assert measure_names(text) == EXPECTED_MEASURES
