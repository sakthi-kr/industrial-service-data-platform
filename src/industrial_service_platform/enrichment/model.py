"""Sparse text classifiers and deterministic structured enrichment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

import joblib  # type: ignore[import-untyped]
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]
from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

from industrial_service_platform.enrichment.dataset import LabeledNote
from industrial_service_platform.enrichment.features import feature_text
from industrial_service_platform.enrichment.schema import (
    COMPONENT_BY_FAULT,
    TEAM_BY_FAULT,
    EnrichmentPrediction,
    is_valid_prediction,
)

UTC = timezone.utc


def _classifier(max_features: int, random_seed: int) -> Any:
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=max_features,
                    sublinear_tf=True,
                    strip_accents="unicode",
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=2000,
                    random_state=random_seed,
                ),
            ),
        ]
    )


@dataclass
class NoteEnrichmentModel:
    """Two classifiers plus deterministic component, team, and summary logic."""

    model_version: str
    fault_model: Any
    priority_model: Any
    trained_at: str

    @classmethod
    def train(
        cls,
        examples: list[LabeledNote],
        *,
        model_version: str,
        max_features: int,
        random_seed: int,
    ) -> NoteEnrichmentModel:
        """Fit fault and priority classifiers on labelled examples."""
        if len(examples) < 20:
            raise ValueError("At least 20 labelled notes are required for training")
        texts = [feature_text(example) for example in examples]
        fault_labels = [example.fault_category for example in examples]
        priority_labels = [example.triage_priority for example in examples]
        if len(set(fault_labels)) < 2 or len(set(priority_labels)) < 2:
            raise ValueError("Training data must contain multiple fault and priority labels")
        fault_model = _classifier(max_features, random_seed)
        priority_model = _classifier(max_features, random_seed)
        fault_model.fit(texts, fault_labels)
        priority_model.fit(texts, priority_labels)
        return cls(
            model_version=model_version,
            fault_model=fault_model,
            priority_model=priority_model,
            trained_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        )

    def predict_labels(self, text: str) -> tuple[str, float, str, float]:
        """Predict fault and priority labels with maximum class probabilities."""
        fault_label = str(self.fault_model.predict([text])[0])
        priority_label = str(self.priority_model.predict([text])[0])
        fault_probabilities = cast(Any, self.fault_model).predict_proba([text])[0]
        priority_probabilities = cast(Any, self.priority_model).predict_proba([text])[0]
        return (
            fault_label,
            float(max(fault_probabilities)),
            priority_label,
            float(max(priority_probabilities)),
        )

    def enrich(
        self,
        example: LabeledNote,
        *,
        processed_at: str | None = None,
        feature_override: str | None = None,
    ) -> EnrichmentPrediction:
        """Generate one validated structured enrichment record."""
        text = feature_override or feature_text(example)
        fault, fault_confidence, priority, priority_confidence = self.predict_labels(text)
        component = COMPONENT_BY_FAULT[fault]
        team = TEAM_BY_FAULT[fault]
        summary = (
            f"{example.note_type.title()} note indicates {fault.replace('_', ' ').lower()} "
            f"at the {component}. Route to {team.replace('_', ' ').lower()} with "
            f"{priority.lower()} priority."
        )
        prediction = EnrichmentPrediction(
            note_id=example.note_id,
            model_version=self.model_version,
            predicted_fault_category=fault,
            predicted_priority=priority,
            predicted_component=component,
            recommended_team=team,
            generated_summary=summary,
            fault_confidence=round(fault_confidence, 6),
            priority_confidence=round(priority_confidence, 6),
            output_valid=False,
            processed_at=processed_at or datetime.now(UTC).replace(microsecond=0).isoformat(),
        )
        return EnrichmentPrediction(
            **{
                **prediction.as_dict(),
                "output_valid": is_valid_prediction(prediction),
            }
        )

    def save(self, path: Path) -> None:
        """Persist the fitted model outside version control."""
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: Path) -> NoteEnrichmentModel:
        """Load a previously fitted model artifact."""
        loaded = joblib.load(path)
        if not isinstance(loaded, cls):
            raise TypeError(f"Unexpected model artifact type: {type(loaded).__name__}")
        return loaded
