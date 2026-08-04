from decimal import Decimal

import pytest

from scripts.reconcile_analytics import normalize_metric_value


def test_normalize_metric_value_converts_decimal_values() -> None:
    assert normalize_metric_value(Decimal("12")) == 12
    assert normalize_metric_value(Decimal("0.625")) == pytest.approx(0.625)


def test_normalize_metric_value_preserves_supported_values() -> None:
    assert normalize_metric_value(None) is None
    assert normalize_metric_value(4) == 4
    assert normalize_metric_value(2.5) == pytest.approx(2.5)


def test_normalize_metric_value_rejects_unexpected_types() -> None:
    with pytest.raises(
        TypeError,
        match="Unsupported KPI value",
    ):
        normalize_metric_value("not-a-number")
