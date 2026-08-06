import csv
from pathlib import Path

from industrial_service_platform.enrichment.dataset import (
    build_labeled_notes,
    derive_triage_priority,
)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_build_labeled_notes_joins_operational_context(tmp_path: Path) -> None:
    _write(
        tmp_path / "technician_notes.csv",
        ["note_id", "service_order_id", "technician_id", "note_type", "note_text", "created_at"],
        [
            {
                "note_id": "NOTE-1",
                "service_order_id": "SORD-1",
                "technician_id": "TECH-1",
                "note_type": "DIAGNOSIS",
                "note_text": "Abnormal vibration at the rotor and bearing assembly.",
                "created_at": "2026-01-01T00:00:00Z",
            }
        ],
    )
    _write(
        tmp_path / "service_orders.csv",
        ["service_order_id", "case_id", "asset_id", "order_type"],
        [
            {
                "service_order_id": "SORD-1",
                "case_id": "CASE-1",
                "asset_id": "ASSET-1",
                "order_type": "CORRECTIVE_REPAIR",
            }
        ],
    )
    _write(
        tmp_path / "customer_cases.csv",
        ["case_id", "fault_category"],
        [{"case_id": "CASE-1", "fault_category": "VIBRATION"}],
    )
    _write(
        tmp_path / "assets.csv",
        ["asset_id", "asset_type", "criticality"],
        [
            {
                "asset_id": "ASSET-1",
                "asset_type": "COMPRESSOR",
                "criticality": "HIGH",
            }
        ],
    )
    examples = build_labeled_notes(tmp_path)
    assert len(examples) == 1
    assert examples[0].fault_category == "VIBRATION"
    assert examples[0].triage_priority == "HIGH"
    assert "asset_type=COMPRESSOR" in examples[0].feature_text()


def test_triage_priority_rule_is_transparent() -> None:
    assert (
        derive_triage_priority(
            asset_criticality="LOW",
            order_type="EMERGENCY_REPAIR",
            note_type="INSPECTION",
            fault_category="OTHER",
        )
        == "CRITICAL"
    )
    assert (
        derive_triage_priority(
            asset_criticality="LOW",
            order_type="INSPECTION",
            note_type="INSPECTION",
            fault_category="OTHER",
        )
        == "LOW"
    )
