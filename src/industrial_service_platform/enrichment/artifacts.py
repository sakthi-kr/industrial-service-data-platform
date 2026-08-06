"""Read and write note-enrichment artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from industrial_service_platform.enrichment.dataset import LabeledNote, write_labeled_notes
from industrial_service_platform.enrichment.schema import EnrichmentPrediction

PREDICTION_FIELDS = [
    "note_id",
    "model_version",
    "predicted_fault_category",
    "predicted_priority",
    "predicted_component",
    "recommended_team",
    "generated_summary",
    "fault_confidence",
    "priority_confidence",
    "output_valid",
    "processed_at",
]


def write_json(path: Path, value: dict[str, Any]) -> None:
    """Write one stable UTF-8 JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_predictions(path: Path, predictions: list[EnrichmentPrediction]) -> None:
    """Write structured predictions to CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=PREDICTION_FIELDS)
        writer.writeheader()
        writer.writerows(prediction.as_dict() for prediction in predictions)


def write_training_artifacts(
    *,
    labeled_dataset_path: Path,
    examples: list[LabeledNote],
    evaluation_path: Path,
    evaluation: dict[str, Any],
    predictions_path: Path,
    predictions: list[EnrichmentPrediction],
    public_sample_directory: Path,
) -> None:
    """Write private full outputs and small tracked evidence samples."""
    write_labeled_notes(labeled_dataset_path, examples)
    write_json(evaluation_path, evaluation)
    write_predictions(predictions_path, predictions)
    public_sample_directory.mkdir(parents=True, exist_ok=True)
    public_evaluation = {
        "model_version": evaluation["model_version"],
        "train_rows": evaluation["train_rows"],
        "test_rows": evaluation["test_rows"],
        "service_order_overlap": evaluation["service_order_overlap"],
        "standard_holdout": evaluation["standard_holdout"],
        "masked_label_challenge": evaluation["masked_label_challenge"],
        "minimum_metrics": evaluation["minimum_metrics"],
        "threshold_results": evaluation["threshold_results"],
        "all_thresholds_passed": evaluation["all_thresholds_passed"],
        "limitations": evaluation["limitations"],
    }
    write_json(public_sample_directory / "evaluation_summary.json", public_evaluation)
    write_predictions(
        public_sample_directory / "sample_predictions.csv",
        predictions[:25],
    )
