"""Shared labels and output validation for note enrichment."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

FAULT_CATEGORIES = (
    "BEARING",
    "CONTROL_SYSTEM",
    "ELECTRICAL",
    "FLOW",
    "INSPECTION",
    "LUBRICATION",
    "OTHER",
    "OVERHEATING",
    "PRESSURE",
    "SEAL",
    "VIBRATION",
)
PRIORITIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

COMPONENT_BY_FAULT = {
    "BEARING": "drive-end bearing",
    "VIBRATION": "rotor and bearing assembly",
    "OVERHEATING": "thermal protection circuit",
    "LUBRICATION": "lubrication system",
    "SEAL": "shaft seal",
    "ELECTRICAL": "motor terminal assembly",
    "CONTROL_SYSTEM": "control cabinet",
    "PRESSURE": "pressure regulation valve",
    "FLOW": "flow path and filter",
    "INSPECTION": "external casing and mounts",
    "OTHER": "serviceable assembly",
}

TEAM_BY_FAULT = {
    "BEARING": "MECHANICAL_SERVICE",
    "VIBRATION": "RELIABILITY_ENGINEERING",
    "OVERHEATING": "MECHANICAL_SERVICE",
    "LUBRICATION": "MECHANICAL_SERVICE",
    "SEAL": "MECHANICAL_SERVICE",
    "ELECTRICAL": "ELECTRICAL_SERVICE",
    "CONTROL_SYSTEM": "AUTOMATION_SERVICE",
    "PRESSURE": "MECHANICAL_SERVICE",
    "FLOW": "PROCESS_SERVICE",
    "INSPECTION": "FIELD_INSPECTION",
    "OTHER": "GENERAL_SERVICE",
}


@dataclass(frozen=True)
class EnrichmentPrediction:
    """One structured prediction ready for CSV or Snowflake publication."""

    note_id: str
    model_version: str
    predicted_fault_category: str
    predicted_priority: str
    predicted_component: str
    recommended_team: str
    generated_summary: str
    fault_confidence: float
    priority_confidence: float
    output_valid: bool
    processed_at: str

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation."""
        return asdict(self)


def is_valid_prediction(prediction: EnrichmentPrediction) -> bool:
    """Validate labels, confidence values, and required text fields."""
    return all(
        (
            bool(prediction.note_id),
            bool(prediction.model_version),
            prediction.predicted_fault_category in FAULT_CATEGORIES,
            prediction.predicted_priority in PRIORITIES,
            prediction.predicted_component
            == COMPONENT_BY_FAULT[prediction.predicted_fault_category],
            prediction.recommended_team == TEAM_BY_FAULT[prediction.predicted_fault_category],
            bool(prediction.generated_summary.strip()),
            0.0 <= prediction.fault_confidence <= 1.0,
            0.0 <= prediction.priority_confidence <= 1.0,
            bool(prediction.processed_at),
        )
    )
