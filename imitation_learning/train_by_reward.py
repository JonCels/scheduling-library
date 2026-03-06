"""
Reward-based policy optimization for vehicle scheduling.

Uses a simple Cross-Entropy Method (CEM) search over linear policy
weights/bias, optimizing schedule strategy score directly.
"""

import argparse
import json
import os
import sys
from statistics import mean
from typing import Dict, List, Tuple

try:
    import numpy as np
except ImportError as exc:
    raise ImportError("numpy is required for train_by_reward.py") from exc

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
if EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, EXAMPLES_DIR)

from imitation_learning.config import DEFAULT_MODEL_PATH  # noqa: E402
from imitation_learning.feature_extractor import FEATURE_NAMES  # noqa: E402
from imitation_learning.policy import LinearCandidatePolicy  # noqa: E402
import imitation_learning.evaluate_model as eval_model  # noqa: E402


def _default_payload() -> Dict:
    n_features = len(FEATURE_NAMES)
    return {
        "model_type": "linear_reward_policy",
        "feature_names": FEATURE_NAMES,
        "weights": [0.0] * n_features,
        "bias": 0.0,
        "feature_mean": [0.0] * n_features,
        "feature_std": [1.0] * n_features,
    }


def _load_init_payload(init_model_path: str, from_scratch: bool) -> Dict:
    payload = _default_payload()
    if from_scratch:
        return payload
    if not os.path.exists(init_model_path):
        print(f"Init model not found at {init_model_path}; starting from scratch.")
        return payload

    with open(init_model_path, "r", encoding="utf-8") as fh:
        loaded = json.load(fh)

    n_features = len(FEATURE_NAMES)
    weights = list(loaded.get("weights", payload["weights"]))
    if len(weights) != n_features:
        weights = (weights + [0.0] * n_features)[:n_features]

    feature_mean = list(loaded.get("feature_mean", payload["feature_mean"]))
    feature_std = list(loaded.get("feature_std", payload["feature_std"]))
    if len(feature_mean) != n_features:
        feature_mean = (feature_mean + [0.0] * n_features)[:n_features]
    if len(feature_std) != n_features:
        feature_std = (feature_std + [1.0] * n_features)[:n_features]

    feature_std = [1.0 if abs(float(x)) < 1e-12 else float(x) for x in feature_std]

    payload.update(
        {
            "weights": [float(x) for x in weights],
            "bias": float(loaded.get("bias", 0.0)),
            "feature_mean": [float(x) for x in feature_mean],
            "feature_std": [float(x) for x in feature_std],
        }
    )
    return payload


def _theta_to_policy(theta: np.ndarray, feature_mean: List[float], feature_std: List[float]) -> LinearCandidatePolicy:
    return LinearCandidatePolicy(
        weights=theta[:-1].tolist(),
        bias=float(theta[-1]),
        feature_mean=feature_mean,
        feature_std=feature_std,
    )


def _evaluate_policy(
    policy: LinearCandidatePolicy,
    seeds: List[int],
    max_ready_eval: int,
    use_repair: bool,
    selected_test_count,
    random_test_pool_size,
    max_greedy_runtime_seconds,
) -> Tuple[float, Dict]:
    rows = []
    for seed in seeds:
        rows.append(
            eval_model._run_one(
                seed=seed,
                candidate_policy=policy,
                max_ready_eval=max_ready_eval,
                use_repair=use_repair,
                selected_test_count=selected_test_count,
                random_test_pool_size=random_test_pool_size,
                max_greedy_runtime_seconds=max_greedy_runtime_seconds,
            )
        )
    avg_score = float(mean(r["strategy_score"] for r in rows))
    details = {
        "avg_strategy_score": avg_score,
        "avg_priority_coverage_percent": float(mean(r["priority_weighted_coverage_percent"] for r in rows)),
        "avg_site_capacity_used_percent": float(mean(r["site_capacity_used_percent"] for r in rows)),
        "avg_scheduled_operations": float(mean(r["scheduled_operations"] for r in rows)),
    }
    return avg_score, details


def _save_payload(path: str, payload: Dict):
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Optimize linear candidate policy by reward (CEM).")
    parser.add_argument("--init-model-path", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output-model-path", default="artifacts/policy/linear_policy_reward_tuned.json")
    parser.add_argument("--from-scratch", action="store_true")

    parser.add_argument("--generations", type=int, default=8)
    parser.add_argument("--population-size", type=int, default=12)
    parser.add_argument("--elite-fraction", type=float, default=0.25)
    parser.add_argument("--init-sigma", type=float, default=0.25)
    parser.add_argument("--min-sigma", type=float, default=0.02)
    parser.add_argument("--seed", type=int, default=1234)

    parser.add_argument("--episodes-per-candidate", type=int, default=2)
    parser.add_argument("--seed-base", type=int, default=10000)

    parser.add_argument("--max-ready-eval", type=int, default=24)
    parser.add_argument("--skip-repair", action="store_true")
    parser.add_argument("--selected-test-count", type=int, default=None)
    parser.add_argument("--random-test-pool-size", type=int, default=None)
    parser.add_argument("--max-greedy-runtime-seconds", type=float, default=None)
    args = parser.parse_args()

    if args.population_size < 2:
        raise ValueError("--population-size must be at least 2")
    if not (0.0 < args.elite_fraction <= 1.0):
        raise ValueError("--elite-fraction must be in (0, 1]")

    init_payload = _load_init_payload(args.init_model_path, args.from_scratch)
    feature_mean = init_payload["feature_mean"]
    feature_std = init_payload["feature_std"]

    theta_mean = np.array(init_payload["weights"] + [init_payload["bias"]], dtype=float)
    theta_dim = theta_mean.shape[0]
    sigma = np.full(theta_dim, float(args.init_sigma), dtype=float)

    rng = np.random.default_rng(args.seed)
    use_repair = not args.skip_repair
    elite_k = max(1, int(round(args.population_size * args.elite_fraction)))

    best_theta = theta_mean.copy()
    best_score = -float("inf")
    history = []

    for generation in range(max(1, args.generations)):
        seeds = [args.seed_base + generation * 1000 + i for i in range(max(1, args.episodes_per_candidate))]

        population = rng.normal(loc=theta_mean, scale=sigma, size=(args.population_size, theta_dim))
        population[0] = theta_mean  # keep incumbent in the pool

        scored = []
        for idx in range(args.population_size):
            theta = population[idx]
            policy = _theta_to_policy(theta, feature_mean, feature_std)
            avg_score, details = _evaluate_policy(
                policy=policy,
                seeds=seeds,
                max_ready_eval=args.max_ready_eval,
                use_repair=use_repair,
                selected_test_count=args.selected_test_count,
                random_test_pool_size=args.random_test_pool_size,
                max_greedy_runtime_seconds=args.max_greedy_runtime_seconds,
            )
            scored.append((avg_score, theta, details))

        scored.sort(key=lambda item: item[0], reverse=True)
        elites = scored[:elite_k]
        elite_thetas = np.stack([item[1] for item in elites], axis=0)

        theta_mean = elite_thetas.mean(axis=0)
        elite_std = elite_thetas.std(axis=0)
        sigma = np.maximum(float(args.min_sigma), elite_std)

        generation_best_score = float(scored[0][0])
        generation_best_details = scored[0][2]
        if generation_best_score > best_score:
            best_score = generation_best_score
            best_theta = scored[0][1].copy()

        history.append(
            {
                "generation": generation,
                "best_avg_strategy_score": generation_best_score,
                "mean_avg_strategy_score": float(mean(item[0] for item in scored)),
                "best_avg_priority_coverage_percent": generation_best_details["avg_priority_coverage_percent"],
            }
        )
        print(
            f"[gen {generation:02d}] best_score={generation_best_score:.4f} "
            f"mean_score={history[-1]['mean_avg_strategy_score']:.4f} "
            f"elite_k={elite_k}"
        )

    tuned_policy = _theta_to_policy(best_theta, feature_mean, feature_std)

    eval_seeds = [args.seed_base + 50000 + i for i in range(max(3, args.episodes_per_candidate))]
    baseline_policy = _theta_to_policy(
        np.array(init_payload["weights"] + [init_payload["bias"]], dtype=float),
        feature_mean,
        feature_std,
    )
    baseline_score, baseline_details = _evaluate_policy(
        policy=baseline_policy,
        seeds=eval_seeds,
        max_ready_eval=args.max_ready_eval,
        use_repair=use_repair,
        selected_test_count=args.selected_test_count,
        random_test_pool_size=args.random_test_pool_size,
        max_greedy_runtime_seconds=args.max_greedy_runtime_seconds,
    )
    tuned_score, tuned_details = _evaluate_policy(
        policy=tuned_policy,
        seeds=eval_seeds,
        max_ready_eval=args.max_ready_eval,
        use_repair=use_repair,
        selected_test_count=args.selected_test_count,
        random_test_pool_size=args.random_test_pool_size,
        max_greedy_runtime_seconds=args.max_greedy_runtime_seconds,
    )

    out_payload = {
        "model_type": "linear_cem_reward_optimization",
        "feature_names": FEATURE_NAMES,
        "weights": best_theta[:-1].tolist(),
        "bias": float(best_theta[-1]),
        "feature_mean": feature_mean,
        "feature_std": feature_std,
        "training_summary": {
            "from_scratch": bool(args.from_scratch),
            "init_model_path": args.init_model_path,
            "generations": int(args.generations),
            "population_size": int(args.population_size),
            "elite_fraction": float(args.elite_fraction),
            "episodes_per_candidate": int(args.episodes_per_candidate),
            "best_train_score": float(best_score),
            "baseline_eval_score": float(baseline_score),
            "tuned_eval_score": float(tuned_score),
            "eval_score_delta": float(tuned_score - baseline_score),
            "history": history,
            "baseline_eval_details": baseline_details,
            "tuned_eval_details": tuned_details,
        },
    }
    _save_payload(args.output_model_path, out_payload)

    print("\nReward optimization complete.")
    print(f"  output_model={args.output_model_path}")
    print(f"  best_train_score={best_score:.4f}")
    print(f"  baseline_eval_score={baseline_score:.4f}")
    print(f"  tuned_eval_score={tuned_score:.4f}")
    print(f"  eval_delta={tuned_score - baseline_score:+.4f}")


if __name__ == "__main__":
    main()
