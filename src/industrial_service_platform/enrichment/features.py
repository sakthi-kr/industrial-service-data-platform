"""Feature construction and lexical-ablation helpers."""

from __future__ import annotations

import re

from industrial_service_platform.enrichment.dataset import LabeledNote
from industrial_service_platform.enrichment.schema import COMPONENT_BY_FAULT


def feature_text(example: LabeledNote) -> str:
    """Return the model input used for both training and prediction."""
    return example.feature_text()


def masked_feature_text(example: LabeledNote) -> str:
    """Mask direct label phrases to measure lexical dependence."""
    text = feature_text(example)
    phrases = {
        example.fault_category.lower(),
        example.fault_category.replace("_", " ").lower(),
        COMPONENT_BY_FAULT[example.fault_category].lower(),
    }
    for phrase in sorted(phrases, key=len, reverse=True):
        text = re.sub(re.escape(phrase), "[masked]", text, flags=re.IGNORECASE)
    return text
