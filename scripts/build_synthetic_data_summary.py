"""Build the synthetic-data summary from generated metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SUMMARY_PATH = Path("data/samples/source_data/generation_summary.json")
VALIDATION_PATH = Path("data/samples/source_data/validation_report.json")
OUTPUT_PATH = Path("docs/synthetic_data_summary.md")


def main() -> int:
    summary = _load_json(SUMMARY_PATH)
    validation = _load_json(VALIDATION_PATH)

    if not validation.get("is_valid"):
        raise RuntimeError("Synthetic-data validation report is not valid")

    row_counts = summary["row_counts"]
    quality = summary["quality_signals"]
    total_rows = sum(int(value) for value in row_counts.values())

    lines = [
        "# Synthetic data summary",
        "",
        "This workflow adds deterministic source data for the industrial service scenario.",
        "The full files remain local, while small samples and validation metadata are tracked.",
        "",
        "## Generated data",
        "",
        "| Dataset | Rows |",
        "|---|---:|",
    ]
    display_names = {
        "assets": "Assets",
        "case_status_history": "Case status history",
        "customer_cases": "Customer cases",
        "customers": "Customers",
        "equipment_alerts": "Equipment alerts",
        "parts": "Parts",
        "service_contracts": "Service contracts",
        "service_costs": "Service costs",
        "service_order_parts": "Service-order parts",
        "service_orders": "Service orders",
        "sites": "Sites",
        "technician_notes": "Technician notes",
        "technicians": "Technicians",
    }
    for dataset_name in sorted(row_counts):
        lines.append(f"| {display_names[dataset_name]} | {int(row_counts[dataset_name]):,} |")

    lines.extend(
        [
            f"| **Total** | **{total_rows:,}** |",
            "",
            "## Validation result",
            "",
            f"- Valid datasets: {validation['is_valid']}",
            f"- Validation issues: {validation['issue_count']}",
            f"- Delayed part lines: {int(quality['delayed_part_lines']):,}",
            f"- Alerts linked to cases: {int(quality['alerts_linked_to_cases']):,}",
            f"- Controlled invalid scenarios: {quality['invalid_example_scenarios']}",
            "",
            "## Reproducibility",
            "",
            "The configuration uses a fixed seed and reporting timestamp. The generator writes",
            "SHA-256 manifests, and the automated tests compare two independent "
            "runs byte for byte.",
            "",
            "## Completion criteria",
            "",
            (
                "The synthetic-data checks pass when generation succeeds and "
                "validation reports zero issues."
            ),
            (
                "All automated tests must pass, and the tracked samples must "
                "match the configured schema."
            ),
        ]
    )

    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Synthetic data summary written to {OUTPUT_PATH}")
    return 0


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required generated file is missing: {path}")
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return content


if __name__ == "__main__":
    raise SystemExit(main())
