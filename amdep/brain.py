"""Synthetic risk scoring for optimizer cost signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from amdep.features import PAIR_FEATURE_COLUMNS, build_pair_features, build_synthetic_labels


@dataclass
class BrainLayer:
    """Demo-only model bundle trained on synthetic labels."""

    models: dict[str, Any]
    feature_columns: list[str]
    synthetic_only: bool = True

    def score_pairs(self, workers: pd.DataFrame, jobs: pd.DataFrame) -> pd.DataFrame:
        features = build_pair_features(workers, jobs)
        x = features[self.feature_columns]
        scored = features.copy()
        scored["attrition_risk_cost"] = _positive_probability(self.models["attrition"], x)
        scored["delay_risk_cost"] = _positive_probability(self.models["delay"], x)
        scored["no_show_risk_cost"] = _positive_probability(self.models["no_show"], x)
        crew_compatibility = _positive_probability(self.models["crew_compatibility"], x)
        scored["crew_incompatibility_cost"] = 1.0 - crew_compatibility
        scored["robotics_suitability_reward"] = _positive_probability(self.models["robotics_suitability"], x)
        return scored


def _positive_probability(model: Any, x: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return model.predict_proba(x)[:, 1]
    scores = model.decision_function(x)
    return 1.0 / (1.0 + np.exp(-scores))


def train_synthetic_brain(workers: pd.DataFrame, jobs: pd.DataFrame, seed: int = 1776) -> BrainLayer:
    """Train synthetic demo models. Accuracy is not evidence of customer performance."""
    features = build_pair_features(workers, jobs)
    training = build_synthetic_labels(features, seed=seed)
    x = training[PAIR_FEATURE_COLUMNS]

    models: dict[str, Any] = {
        "attrition": Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=1200, class_weight="balanced", random_state=seed)),
            ]
        ),
        "delay": HistGradientBoostingClassifier(max_iter=120, learning_rate=0.07, random_state=seed),
        "crew_compatibility": RandomForestClassifier(
            n_estimators=120,
            max_depth=8,
            min_samples_leaf=10,
            random_state=seed,
            class_weight="balanced_subsample",
        ),
        "no_show": Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", LogisticRegression(max_iter=1200, class_weight="balanced", random_state=seed + 3)),
            ]
        ),
        "robotics_suitability": RandomForestClassifier(
            n_estimators=100,
            max_depth=7,
            min_samples_leaf=8,
            random_state=seed + 5,
            class_weight="balanced_subsample",
        ),
    }
    targets = {
        "attrition": "attrition_risk_label",
        "delay": "delay_risk_label",
        "crew_compatibility": "crew_compatible_label",
        "no_show": "no_show_risk_label",
        "robotics_suitability": "robotics_suitable_label",
    }
    for name, model in models.items():
        model.fit(x, training[targets[name]])
    return BrainLayer(models=models, feature_columns=list(PAIR_FEATURE_COLUMNS))


def brain_layer_summary() -> list[str]:
    return [
        "Rules define operational reality: skills, certifications, headcount, capacity, geography, and asset availability.",
        "Synthetic ML models predict hidden risk terms for demo purposes only.",
        "The optimizer consumes risk scores as costs and rewards while honoring hard constraints.",
        "Operations approves, rejects, or overrides recommendations.",
        "Overrides and outcomes become future supervised training data.",
    ]
