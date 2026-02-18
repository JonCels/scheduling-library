"""
Simple linear candidate-ranking policy for imitation learning.
"""

import json
from typing import Dict, List, Optional

from imitation_learning.feature_extractor import candidate_to_feature_vector


class LinearCandidatePolicy:
    """
    Scores candidate actions with a learned linear model.
    """

    def __init__(self, weights: List[float], bias: float, feature_mean: List[float], feature_std: List[float]):
        self.weights = [float(w) for w in weights]
        self.bias = float(bias)
        self.feature_mean = [float(x) for x in feature_mean]
        self.feature_std = [float(x) for x in feature_std]

    @classmethod
    def load(cls, model_path: str) -> "LinearCandidatePolicy":
        with open(model_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return cls(
            weights=payload["weights"],
            bias=payload["bias"],
            feature_mean=payload["feature_mean"],
            feature_std=payload["feature_std"],
        )

    def score_candidate(self, candidate: Dict) -> float:
        x = candidate_to_feature_vector(candidate)
        z = []
        for i, x_i in enumerate(x):
            std_i = self.feature_std[i] if i < len(self.feature_std) else 1.0
            mean_i = self.feature_mean[i] if i < len(self.feature_mean) else 0.0
            z.append((x_i - mean_i) / std_i if std_i > 0 else x_i - mean_i)
        return sum(w * z_i for w, z_i in zip(self.weights, z)) + self.bias

    def choose_candidate(self, candidates: List[Dict]) -> Optional[Dict]:
        if not candidates:
            return None
        best = None
        best_score = None
        for candidate in candidates:
            predicted = self.score_candidate(candidate)
            if best is None or predicted > best_score:
                best = candidate
                best_score = predicted
        return best

