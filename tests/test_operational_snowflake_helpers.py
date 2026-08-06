from datetime import datetime, timezone

import pytest

from industrial_service_platform.operations.snowflake import (
    _relation,
    _to_bool,
    _to_datetime,
)


def test_snowflake_relation_validation() -> None:
    assert (
        _relation("industrial_service_db.raw.erp_customers")
        == "INDUSTRIAL_SERVICE_DB.RAW.ERP_CUSTOMERS"
    )
    with pytest.raises(ValueError, match="Unsafe Snowflake relation"):
        _relation("RAW.ERP_CUSTOMERS; DROP TABLE X")


def test_snowflake_value_normalization() -> None:
    assert _to_bool(True) is True
    assert _to_bool("false") is False
    value = datetime(2026, 8, 6, 12, 0)
    assert _to_datetime(value) == value.replace(tzinfo=timezone.utc)
