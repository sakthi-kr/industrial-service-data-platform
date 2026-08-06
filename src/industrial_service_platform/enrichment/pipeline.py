"""End-to-end model training, evaluation, and prediction."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from industrial_service_platform.enrichment.artifacts import write_training_artifacts
from industrial_service_platform.enrichment.config import EnrichmentConfig
from industrial_service_platform.enrichment.dataset import build_labeled_notes
from industrial_service_platform.enrichment.evaluation import evaluate_model, grouped_split
from industrial_service_platform.enrichment.model import NoteEnrichmentModel
from industrial_service_platform.enrichment.schema import EnrichmentPrediction

UTC = timezone.utc


def train_and_evaluate(config: EnrichmentConfig) -> dict[str, Any]:
    """Build labels, evaluate a holdout model, then fit and save the final model."""
    examples = build_labeled_notes(config.source_directory)
    split = grouped_split(
        examples,
        test_size=config.test_size,
        random_seed=config.random_seed,
    )
    evaluation_model = NoteEnrichmentModel.train(
        split.train,
        model_version=config.model_version,
        max_features=config.max_features,
        random_seed=config.random_seed,
    )
    evaluation = evaluate_model(evaluation_model, split, config.minimum_metrics)
    final_model = NoteEnrichmentModel.train(
        examples,
        model_version=config.model_version,
        max_features=config.max_features,
        random_seed=config.random_seed,
    )
    final_model.save(config.model_path)
    processed_at = datetime.now(UTC).replace(microsecond=0).isoformat()
    predictions: list[EnrichmentPrediction] = [
        final_model.enrich(example, processed_at=processed_at) for example in examples
    ]
    evaluation["all_prediction_rows"] = len(predictions)
    evaluation["all_prediction_outputs_valid"] = all(
        prediction.output_valid for prediction in predictions
    )
    write_training_artifacts(
        labeled_dataset_path=config.labeled_dataset_path,
        examples=examples,
        evaluation_path=config.evaluation_path,
        evaluation=evaluation,
        predictions_path=config.predictions_path,
        predictions=predictions,
        public_sample_directory=config.public_sample_directory,
    )
    return evaluation
