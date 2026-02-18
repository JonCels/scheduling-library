"""
Train a simple linear imitation policy from recorded trajectories.
"""

import argparse
import json
import os
from glob import glob
from typing import Dict, List, Tuple

try:
    import numpy as np
except ImportError as exc:
    raise ImportError("numpy is required for train_model.py") from exc

from imitation_learning.config import DEFAULT_DATA_DIR, DEFAULT_MODEL_PATH
from imitation_learning.feature_extractor import FEATURE_NAMES, build_training_rows_from_decision


def _load_decisions(data_dir: str) -> List[Dict]:
    decisions = []
    for path in sorted(glob(os.path.join(data_dir, "*.jsonl"))):
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("record_type") == "decision":
                    decisions.append(row)
    return decisions


def _build_matrix(decisions: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
    x_rows = []
    y_rows = []
    for d in decisions:
        rows, labels = build_training_rows_from_decision(d)
        x_rows.extend(rows)
        y_rows.extend(labels)
    if not x_rows:
        raise ValueError("No training rows found. Generate trajectory data first.")
    x = np.array(x_rows, dtype=float)
    y = np.array(y_rows, dtype=float)
    return x, y


def train_linear_policy(data_dir: str, model_path: str, ridge_lambda: float = 1e-3) -> Dict:
    decisions = _load_decisions(data_dir)
    x, y = _build_matrix(decisions)

    feature_mean = x.mean(axis=0)
    feature_std = x.std(axis=0)
    feature_std[feature_std == 0.0] = 1.0
    z = (x - feature_mean) / feature_std

    # Closed-form ridge regression with bias term.
    ones = np.ones((z.shape[0], 1), dtype=float)
    design = np.concatenate([z, ones], axis=1)
    reg = ridge_lambda * np.eye(design.shape[1], dtype=float)
    reg[-1, -1] = 0.0  # do not regularize bias
    w_full = np.linalg.solve(design.T @ design + reg, design.T @ y)

    weights = w_full[:-1].tolist()
    bias = float(w_full[-1])
    preds = design @ w_full
    mse = float(np.mean((preds - y) ** 2))

    payload = {
        "model_type": "linear_ridge_regression",
        "feature_names": FEATURE_NAMES,
        "weights": weights,
        "bias": bias,
        "feature_mean": feature_mean.tolist(),
        "feature_std": feature_std.tolist(),
        "train_rows": int(len(y)),
        "train_decisions": int(len(decisions)),
        "train_mse": mse,
    }
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    return payload


def main():
    parser = argparse.ArgumentParser(description="Train imitation-learning linear policy.")
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--ridge-lambda", type=float, default=1e-3)
    args = parser.parse_args()

    result = train_linear_policy(
        data_dir=args.data_dir,
        model_path=args.model_path,
        ridge_lambda=args.ridge_lambda,
    )
    print("Trained policy:")
    print(f"  rows={result['train_rows']}, decisions={result['train_decisions']}, mse={result['train_mse']:.6f}")
    print(f"  saved_to={args.model_path}")


if __name__ == "__main__":
    main()

