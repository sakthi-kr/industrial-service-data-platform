"""Compare independent Python KPIs with the Snowflake analytics mart."""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from industrial_service_platform.analytics.reference_metrics import (
    KPI_NAMES,
    MetricValue,
    compare_metric_sets,
    compute_reference_metrics,
)
from industrial_service_platform.ingestion.config import SnowflakeSettings
from industrial_service_platform.ingestion.connection import connect_once

CONFIG_PATH = Path("config/analytics_reconciliation.json")


def load_configuration(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the tracked reconciliation configuration."""
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_metric_value(value: object) -> MetricValue:
    """Convert Snowflake numeric values into JSON-safe Python numbers."""
    if value is None:
        return None

    if isinstance(value, bool):
        raise TypeError("Boolean values are not valid KPI values")

    if isinstance(value, int | float):
        return value

    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return int(value)
        return float(value)

    raise TypeError(f"Unsupported KPI value returned by Snowflake: {type(value).__name__}")


def load_warehouse_metrics(
    configuration: dict[str, Any],
) -> dict[str, MetricValue]:
    """Read the single KPI summary row using the analyst role."""
    environment = dict(os.environ)
    environment["SNOWFLAKE_ROLE"] = str(configuration["snowflake_role"])

    settings = SnowflakeSettings.from_environment(
        Path(".env"),
        environ=environment,
    )

    connection = connect_once(settings)
    cursor = connection.cursor()
    relation = str(configuration["warehouse_relation"])

    try:
        cursor.execute(f"select {', '.join(KPI_NAMES)} from {relation}")
        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(f"No KPI row was returned from {relation}")

        return {name: normalize_metric_value(row[index]) for index, name in enumerate(KPI_NAMES)}
    finally:
        cursor.close()
        connection.close()


def main() -> int:
    """Run the reconciliation and write a local JSON report."""
    configuration = load_configuration()

    reporting_as_of = datetime.fromisoformat(
        str(configuration["reporting_as_of"]).replace(
            "Z",
            "+00:00",
        )
    )

    reference = compute_reference_metrics(
        Path(str(configuration["source_directory"])),
        reporting_as_of,
    )

    warehouse = load_warehouse_metrics(configuration)

    comparisons = compare_metric_sets(
        reference,
        warehouse,
        configuration["tolerances"],
    )

    report = {
        "reporting_as_of": configuration["reporting_as_of"],
        "all_metrics_passed": all(item["passed"] for item in comparisons),
        "metrics": comparisons,
    }

    rendered_report = json.dumps(report, indent=2)

    output_path = Path(str(configuration["output_path"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        rendered_report + "\n",
        encoding="utf-8",
    )

    print(rendered_report)

    return 0 if report["all_metrics_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
