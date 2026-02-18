"""
Feature extraction for candidate scheduling actions.
"""

from typing import Dict, List, Tuple


# Keep feature names stable so saved model weights remain interpretable.
FEATURE_NAMES = [
    "priority_rank_inv",
    "priority_bucket_inv",
    "duration_hours_inv",
    "effective_duration_hours_inv",
    "slack_hours_inv",
    "site_options_inv",
    "avg_site_importance",
    "descendant_ratio",
    "heuristic_score",
]


def candidate_to_feature_vector(candidate: Dict) -> List[float]:
    """
    Convert a candidate dict into a numeric feature vector.
    """
    priority_rank = float(candidate.get("priority_rank", 1e9))
    priority_bucket = float(candidate.get("priority", 5))
    duration_hours = max(float(candidate.get("duration_hours", 0.0)), 0.01)
    effective_duration_hours = max(float(candidate.get("effective_duration_hours", 0.0)), 0.01)
    slack_hours = max(float(candidate.get("slack_hours", 0.0)), 0.0)
    site_options = max(float(candidate.get("site_options", 1.0)), 1.0)
    avg_site_importance = float(candidate.get("avg_site_importance", 0.0))
    descendant_ratio = float(candidate.get("descendant_ratio", 0.0))
    heuristic_score = float(candidate.get("score", 0.0))

    return [
        1.0 / (1.0 + priority_rank),
        1.0 / (1.0 + priority_bucket),
        1.0 / duration_hours,
        1.0 / effective_duration_hours,
        1.0 / (1.0 + slack_hours),
        1.0 / site_options,
        avg_site_importance,
        descendant_ratio,
        heuristic_score,
    ]


def build_training_rows_from_decision(decision: Dict) -> Tuple[List[List[float]], List[float]]:
    """
    Convert one recorded decision into supervised rows.

    Target convention:
    - chosen candidate => 1.0
    - non-chosen candidate => 0.0
    """
    candidates = decision.get("candidates", [])
    selected_operation_id = decision.get("selected_operation_id")
    rows = []
    labels = []
    for c in candidates:
        rows.append(candidate_to_feature_vector(c))
        labels.append(1.0 if c.get("operation_id") == selected_operation_id else 0.0)
    return rows, labels

