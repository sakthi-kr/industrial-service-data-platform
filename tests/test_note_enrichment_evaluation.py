from industrial_service_platform.enrichment.config import MetricThresholds
from industrial_service_platform.enrichment.dataset import LabeledNote
from industrial_service_platform.enrichment.evaluation import evaluate_model, grouped_split
from industrial_service_platform.enrichment.model import NoteEnrichmentModel
from industrial_service_platform.enrichment.schema import COMPONENT_BY_FAULT, TEAM_BY_FAULT


def _data() -> list[LabeledNote]:
    examples: list[LabeledNote] = []
    faults = list(COMPONENT_BY_FAULT)
    priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for repetition in range(14):
        for position, fault in enumerate(faults):
            priority = priorities[(position + repetition) % 4]
            component = COMPONENT_BY_FAULT[fault]
            index = len(examples)
            examples.append(
                LabeledNote(
                    note_id=f"N-{index}",
                    service_order_id=f"O-{index}",
                    note_type="DIAGNOSIS",
                    note_text=f"Observed {fault.lower()} around the {component}.",
                    asset_type="COMPRESSOR",
                    asset_criticality=priority,
                    order_type="CORRECTIVE_REPAIR",
                    fault_category=fault,
                    triage_priority=priority,
                    component=component,
                    recommended_team=TEAM_BY_FAULT[fault],
                )
            )
    return examples


def test_evaluation_reports_standard_and_masked_results() -> None:
    data = _data()
    split = grouped_split(data, test_size=0.25, random_seed=9)
    model = NoteEnrichmentModel.train(
        split.train,
        model_version="test-v1",
        max_features=4000,
        random_seed=9,
    )
    report = evaluate_model(
        model,
        split,
        MetricThresholds(
            fault_macro_f1=0.5,
            priority_macro_f1=0.5,
            component_accuracy=0.5,
            structured_output_validity_rate=1.0,
        ),
    )
    assert report["service_order_overlap"] == 0
    assert report["all_thresholds_passed"]
    assert "masked_label_challenge" in report
