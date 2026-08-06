from industrial_service_platform.enrichment.dataset import LabeledNote
from industrial_service_platform.enrichment.evaluation import grouped_split
from industrial_service_platform.enrichment.features import masked_feature_text
from industrial_service_platform.enrichment.model import NoteEnrichmentModel
from industrial_service_platform.enrichment.schema import (
    COMPONENT_BY_FAULT,
    TEAM_BY_FAULT,
    is_valid_prediction,
)

FAULTS = list(COMPONENT_BY_FAULT)
PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _example(index: int, fault: str, priority: str) -> LabeledNote:
    component = COMPONENT_BY_FAULT[fault]
    return LabeledNote(
        note_id=f"NOTE-{index:04d}",
        service_order_id=f"SORD-{index:04d}",
        note_type="DIAGNOSIS",
        note_text=f"Measurements confirmed abnormal {fault.lower()} at the {component}.",
        asset_type="COMPRESSOR",
        asset_criticality=priority,
        order_type="CORRECTIVE_REPAIR",
        fault_category=fault,
        triage_priority=priority,
        component=component,
        recommended_team=TEAM_BY_FAULT[fault],
    )


def _examples() -> list[LabeledNote]:
    rows: list[LabeledNote] = []
    index = 0
    for repetition in range(12):
        for fault_index, fault in enumerate(FAULTS):
            priority = PRIORITIES[(fault_index + repetition) % len(PRIORITIES)]
            rows.append(_example(index, fault, priority))
            index += 1
    return rows


def test_grouped_split_has_no_service_order_overlap() -> None:
    split = grouped_split(_examples(), test_size=0.25, random_seed=12)
    train_orders = {item.service_order_id for item in split.train}
    test_orders = {item.service_order_id for item in split.test}
    assert not train_orders & test_orders
    assert {item.fault_category for item in split.test} == set(FAULTS)


def test_model_produces_valid_structured_output() -> None:
    examples = _examples()
    model = NoteEnrichmentModel.train(
        examples,
        model_version="test-v1",
        max_features=3000,
        random_seed=4,
    )
    prediction = model.enrich(examples[0], processed_at="2026-08-06T00:00:00+00:00")
    assert prediction.output_valid
    assert is_valid_prediction(prediction)
    assert prediction.predicted_component == COMPONENT_BY_FAULT[prediction.predicted_fault_category]


def test_masked_feature_text_removes_direct_fault_and_component() -> None:
    example = _example(1, "VIBRATION", "HIGH")
    masked = masked_feature_text(example).lower()
    assert "vibration" not in masked
    assert "rotor and bearing assembly" not in masked
    assert "[masked]" in masked
