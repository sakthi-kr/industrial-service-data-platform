"""Build labelled technician-note examples from generated source files."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from industrial_service_platform.enrichment.schema import COMPONENT_BY_FAULT, TEAM_BY_FAULT


@dataclass(frozen=True)
class LabeledNote:
    """One labelled enrichment example with operational context."""

    note_id: str
    service_order_id: str
    note_type: str
    note_text: str
    asset_type: str
    asset_criticality: str
    order_type: str
    fault_category: str
    triage_priority: str
    component: str
    recommended_team: str

    def feature_text(self) -> str:
        """Combine free text with permitted operational context."""
        return (
            f"note_type={self.note_type} "
            f"asset_type={self.asset_type} "
            f"criticality={self.asset_criticality} "
            f"order_type={self.order_type} "
            f"text={self.note_text}"
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a CSV-ready record."""
        return asdict(self)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(f"Required enrichment source file is missing: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _index(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value:
            raise ValueError(f"Missing key {key!r} in enrichment source row")
        if value in indexed:
            raise ValueError(f"Duplicate key {value!r} in enrichment source")
        indexed[value] = row
    return indexed


def derive_triage_priority(
    *,
    asset_criticality: str,
    order_type: str,
    note_type: str,
    fault_category: str,
) -> str:
    """Assign a transparent synthetic triage label for evaluation."""
    if order_type == "EMERGENCY_REPAIR" or asset_criticality == "CRITICAL":
        return "CRITICAL"
    if asset_criticality == "HIGH" or fault_category in {
        "CONTROL_SYSTEM",
        "ELECTRICAL",
        "OVERHEATING",
    }:
        return "HIGH"
    if asset_criticality == "MEDIUM" or note_type in {"DIAGNOSIS", "REPAIR"}:
        return "MEDIUM"
    return "LOW"


def build_labeled_notes(source_directory: Path) -> list[LabeledNote]:
    """Join generated source files into a reproducible labelled dataset."""
    notes = _read_csv(source_directory / "technician_notes.csv")
    orders = _index(_read_csv(source_directory / "service_orders.csv"), "service_order_id")
    cases = _index(_read_csv(source_directory / "customer_cases.csv"), "case_id")
    assets = _index(_read_csv(source_directory / "assets.csv"), "asset_id")

    examples: list[LabeledNote] = []
    for note in notes:
        order = orders.get(note.get("service_order_id", ""))
        if order is None:
            raise ValueError(f"Unknown service order for note {note.get('note_id', '')}")
        asset = assets.get(order.get("asset_id", ""))
        if asset is None:
            raise ValueError(f"Unknown asset for note {note.get('note_id', '')}")
        case_id = order.get("case_id", "")
        linked_case = cases.get(case_id) if case_id else None
        fault_category = (
            linked_case.get("fault_category", "") if linked_case is not None else "INSPECTION"
        ) or "OTHER"
        note_text = note.get("note_text", "").strip()
        if not note_text:
            raise ValueError(f"Empty technician note: {note.get('note_id', '')}")
        priority = derive_triage_priority(
            asset_criticality=asset["criticality"],
            order_type=order["order_type"],
            note_type=note["note_type"],
            fault_category=fault_category,
        )
        examples.append(
            LabeledNote(
                note_id=note["note_id"],
                service_order_id=note["service_order_id"],
                note_type=note["note_type"],
                note_text=note_text,
                asset_type=asset["asset_type"],
                asset_criticality=asset["criticality"],
                order_type=order["order_type"],
                fault_category=fault_category,
                triage_priority=priority,
                component=COMPONENT_BY_FAULT[fault_category],
                recommended_team=TEAM_BY_FAULT[fault_category],
            )
        )
    return examples


def write_labeled_notes(path: Path, examples: list[LabeledNote]) -> None:
    """Write the generated labelled dataset outside version control."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(LabeledNote.__dataclass_fields__)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(example.as_dict() for example in examples)
