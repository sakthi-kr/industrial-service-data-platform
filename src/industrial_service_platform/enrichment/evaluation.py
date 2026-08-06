"""Leakage-aware evaluation for technician-note enrichment."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from sklearn.metrics import accuracy_score, f1_score  # type: ignore[import-untyped]
from sklearn.model_selection import GroupShuffleSplit  # type: ignore[import-untyped]

from industrial_service_platform.enrichment.config import MetricThresholds
from industrial_service_platform.enrichment.dataset import LabeledNote
from industrial_service_platform.enrichment.features import feature_text, masked_feature_text
from industrial_service_platform.enrichment.model import NoteEnrichmentModel
from industrial_service_platform.enrichment.schema import is_valid_prediction


@dataclass(frozen=True)
class DatasetSplit:
    """Train and test examples with non-overlapping service orders."""

    train: list[LabeledNote]
    test: list[LabeledNote]


def grouped_split(
    examples: list[LabeledNote],
    *,
    test_size: float,
    random_seed: int,
) -> DatasetSplit:
    """Split by service order and preserve all labels in both partitions."""
    labels_fault = {example.fault_category for example in examples}
    labels_priority = {example.triage_priority for example in examples}
    groups = [example.service_order_id for example in examples]
    splitter = GroupShuffleSplit(
        n_splits=50,
        test_size=test_size,
        random_state=random_seed,
    )
    placeholder = list(range(len(examples)))
    for train_indices, test_indices in splitter.split(placeholder, groups=groups):
        train = [examples[int(index)] for index in train_indices]
        test = [examples[int(index)] for index in test_indices]
        if {item.fault_category for item in train} != labels_fault:
            continue
        if {item.fault_category for item in test} != labels_fault:
            continue
        if {item.triage_priority for item in train} != labels_priority:
            continue
        if {item.triage_priority for item in test} != labels_priority:
            continue
        train_groups = {item.service_order_id for item in train}
        test_groups = {item.service_order_id for item in test}
        if train_groups & test_groups:
            raise RuntimeError("Grouped split leaked service orders across partitions")
        return DatasetSplit(train=train, test=test)
    raise RuntimeError("Could not create a grouped split containing every target label")


def _metric_values(
    model: NoteEnrichmentModel,
    examples: list[LabeledNote],
    *,
    masked: bool,
) -> dict[str, float]:
    actual_fault: list[str] = []
    predicted_fault: list[str] = []
    actual_priority: list[str] = []
    predicted_priority: list[str] = []
    component_matches = 0
    team_matches = 0
    valid_outputs = 0
    started = time.perf_counter()
    for example in examples:
        override = masked_feature_text(example) if masked else feature_text(example)
        prediction = model.enrich(example, feature_override=override)
        actual_fault.append(example.fault_category)
        predicted_fault.append(prediction.predicted_fault_category)
        actual_priority.append(example.triage_priority)
        predicted_priority.append(prediction.predicted_priority)
        component_matches += int(prediction.predicted_component == example.component)
        team_matches += int(prediction.recommended_team == example.recommended_team)
        valid_outputs += int(is_valid_prediction(prediction) and prediction.output_valid)
    elapsed = time.perf_counter() - started
    count = len(examples)
    return {
        "fault_macro_f1": float(
            f1_score(actual_fault, predicted_fault, average="macro", zero_division=0)
        ),
        "fault_accuracy": float(accuracy_score(actual_fault, predicted_fault)),
        "priority_macro_f1": float(
            f1_score(actual_priority, predicted_priority, average="macro", zero_division=0)
        ),
        "priority_accuracy": float(accuracy_score(actual_priority, predicted_priority)),
        "component_accuracy": component_matches / count,
        "recommended_team_accuracy": team_matches / count,
        "structured_output_validity_rate": valid_outputs / count,
        "failure_rate": (count - valid_outputs) / count,
        "mean_latency_ms": elapsed * 1000.0 / count,
    }


def evaluate_model(
    model: NoteEnrichmentModel,
    split: DatasetSplit,
    thresholds: MetricThresholds,
) -> dict[str, Any]:
    """Evaluate standard and lexical-ablation test sets."""
    standard = _metric_values(model, split.test, masked=False)
    masked = _metric_values(model, split.test, masked=True)
    threshold_results = {
        name: standard[name] >= value for name, value in thresholds.as_dict().items()
    }
    return {
        "model_version": model.model_version,
        "trained_at": model.trained_at,
        "train_rows": len(split.train),
        "test_rows": len(split.test),
        "train_service_orders": len({item.service_order_id for item in split.train}),
        "test_service_orders": len({item.service_order_id for item in split.test}),
        "service_order_overlap": len(
            {item.service_order_id for item in split.train}
            & {item.service_order_id for item in split.test}
        ),
        "standard_holdout": {name: round(value, 6) for name, value in standard.items()},
        "masked_label_challenge": {name: round(value, 6) for name, value in masked.items()},
        "minimum_metrics": thresholds.as_dict(),
        "threshold_results": threshold_results,
        "all_thresholds_passed": all(threshold_results.values()),
        "limitations": [
            "Labels are derived from synthetic operational records rather than human annotation.",
            "Generated notes often contain direct fault or component phrases.",
            "The masked-label challenge is reported to expose lexical dependence.",
            "The generated summary is deterministic and does not use an external language model.",
        ],
    }
