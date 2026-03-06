"""
Quick evaluator for a trained imitation policy.
"""

import argparse
import os
import sys
from statistics import mean

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
EXAMPLES_DIR = os.path.join(ROOT_DIR, "examples")
if EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, EXAMPLES_DIR)

import examples.example_vehicle_testing as evt  # noqa: E402
from examples.vehicle_testing_model import build_vehicle_testing_problem  # noqa: E402
from examples.constraint_config import SCHEDULE_CONFIG  # noqa: E402
from imitation_learning.policy import LinearCandidatePolicy  # noqa: E402


def _run_one(
    seed,
    candidate_policy,
    max_ready_eval: int,
    use_repair: bool,
    selected_test_count=None,
    random_test_pool_size=None,
    max_greedy_runtime_seconds=None,
    ml_top_k=None,
    ml_fallback_expand=True,
):
    SCHEDULE_CONFIG["random_test_seed"] = seed
    if selected_test_count is not None:
        SCHEDULE_CONFIG["selected_test_count"] = int(selected_test_count)
    if random_test_pool_size is not None:
        SCHEDULE_CONFIG["random_test_pool_size"] = int(random_test_pool_size)
    schedule, tests, sites, _vehicles, start_date, end_date = build_vehicle_testing_problem()
    children_by_op = evt._build_children_map(tests)
    descendant_counts = evt._build_descendant_counts(children_by_op)
    evt.compute_priority_ranks_naive(tests)

    score_config = {
        "priority_bucket_weights": {1: 30.0, 2: 15.0, 3: 6.0, 4: 2.0, 5: 1.0},
        "duration_exponent_gamma": 0.6,
        "priority_coverage_weight": 0.80,
        "site_utilization_weight": 0.20,
    }

    unscheduled = evt._run_greedy_schedule(
        schedule,
        start_date,
        end_date,
        descendant_counts,
        mode="enhanced_dispatch",
        max_ready_eval=max_ready_eval,
        max_runtime_seconds=max_greedy_runtime_seconds,
        candidate_policy=candidate_policy,
        ml_top_k=ml_top_k,
        ml_fallback_expand=ml_fallback_expand,
    )
    if use_repair:
        unscheduled, _ = evt._run_repair_pass(
            schedule,
            unscheduled,
            score_config,
            children_by_op,
            max_candidates=24,
            max_assignments_per_candidate=16,
            max_starts_per_assignment=24,
        )
    metrics = evt._evaluate_schedule_metrics(
        schedule, list(schedule.operations.values()), sites, start_date, end_date, score_config
    )
    return {
        "seed": seed,
        "scheduled_operations": len(schedule.get_scheduled_operations()),
        "unscheduled_operations": len(unscheduled),
        "strategy_score": metrics["strategy_score"],
        "priority_weighted_coverage_percent": metrics["priority_weighted_coverage_percent"],
        "site_capacity_used_percent": metrics["site_capacity_used_percent"],
    }


def _summarize(rows, label):
    print(f"\n{label}:")
    print(f"  runs={len(rows)}")
    print(f"  avg_strategy_score={mean(r['strategy_score'] for r in rows):.4f}")
    print(f"  avg_priority_coverage={mean(r['priority_weighted_coverage_percent'] for r in rows):.2f}%")
    print(f"  avg_site_capacity_used={mean(r['site_capacity_used_percent'] for r in rows):.2f}%")
    print(f"  avg_scheduled_ops={mean(r['scheduled_operations'] for r in rows):.2f}")


def main():
    parser = argparse.ArgumentParser(description="Compare heuristic dispatch vs learned ML dispatch.")
    parser.add_argument("--model-path", default="artifacts/policy/linear_policy.json")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--seed-base", type=int, default=1000)
    parser.add_argument("--max-ready-eval", type=int, default=24)
    parser.add_argument("--skip-repair", action="store_true")
    parser.add_argument("--selected-test-count", type=int, default=None)
    parser.add_argument("--random-test-pool-size", type=int, default=None)
    parser.add_argument("--max-greedy-runtime-seconds", type=float, default=None)
    parser.add_argument("--ml-top-k", type=int, default=None)
    parser.add_argument("--no-ml-fallback-expand", action="store_true")
    args = parser.parse_args()

    policy = LinearCandidatePolicy.load(args.model_path)

    use_repair = not args.skip_repair
    ml_fallback_expand = not args.no_ml_fallback_expand
    baseline_rows = []
    ml_rows = []
    for idx in range(max(1, args.episodes)):
        seed = args.seed_base + idx
        baseline_rows.append(
            _run_one(
                seed,
                candidate_policy=None,
                max_ready_eval=args.max_ready_eval,
                use_repair=use_repair,
                selected_test_count=args.selected_test_count,
                random_test_pool_size=args.random_test_pool_size,
                max_greedy_runtime_seconds=args.max_greedy_runtime_seconds,
                ml_top_k=None,
                ml_fallback_expand=True,
            )
        )
        ml_rows.append(
            _run_one(
                seed,
                candidate_policy=policy,
                max_ready_eval=args.max_ready_eval,
                use_repair=use_repair,
                selected_test_count=args.selected_test_count,
                random_test_pool_size=args.random_test_pool_size,
                max_greedy_runtime_seconds=args.max_greedy_runtime_seconds,
                ml_top_k=args.ml_top_k,
                ml_fallback_expand=ml_fallback_expand,
            )
        )

    _summarize(baseline_rows, "Heuristic baseline (enhanced_dispatch + repair)")
    _summarize(ml_rows, "ML policy (learned dispatch + repair)")

    score_deltas = [m["strategy_score"] - b["strategy_score"] for b, m in zip(baseline_rows, ml_rows)]
    cov_deltas = [
        m["priority_weighted_coverage_percent"] - b["priority_weighted_coverage_percent"]
        for b, m in zip(baseline_rows, ml_rows)
    ]
    print("\nDelta (ML - baseline):")
    print(f"  avg_strategy_score_delta={mean(score_deltas):+.4f}")
    print(f"  avg_priority_coverage_delta={mean(cov_deltas):+.2f}%")


if __name__ == "__main__":
    main()

