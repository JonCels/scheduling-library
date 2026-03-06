"""
Generate imitation-learning trajectory data from heuristic scheduling.
"""

import argparse
import os
import sys
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from imitation_learning.config import DEFAULT_DATA_DIR  # noqa: E402
from imitation_learning.data_collection import TrajectoryRecorder  # noqa: E402
import example_vehicle_testing as evt  # noqa: E402
from vehicle_testing_model import build_vehicle_testing_problem  # noqa: E402
from constraint_config import SCHEDULE_CONFIG  # noqa: E402


def _collect_one_episode(output_dir, episode_idx, seed, scheduler_mode, use_repair):
    if seed is not None:
        SCHEDULE_CONFIG["random_test_seed"] = int(seed)

    schedule, tests, sites, _vehicles, start_date, end_date = build_vehicle_testing_problem()
    children_by_op = evt._build_children_map(tests)
    descendant_counts = evt._build_descendant_counts(children_by_op)
    evt.compute_priority_ranks_naive(tests)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(
        output_dir,
        f"episode_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{episode_idx:03d}.jsonl",
    )

    recorder = TrajectoryRecorder(
        output_path=out_path,
        run_metadata={
            "ranking_strategy": "naive",
            "scheduler_mode": scheduler_mode,
            "random_test_seed": seed,
            "notes": "expert-trajectory",
        },
    )

    score_config = {
        "priority_bucket_weights": {1: 30.0, 2: 15.0, 3: 6.0, 4: 2.0, 5: 1.0},
        "duration_exponent_gamma": 0.6,
        "priority_coverage_weight": 0.80,
        "site_utilization_weight": 0.20,
    }

    def decision_callback(payload):
        recorder.record_decision(payload)

    unscheduled = evt._run_greedy_schedule(
        schedule,
        start_date,
        end_date,
        descendant_counts,
        mode=scheduler_mode,
        decision_callback=decision_callback,
    )
    if use_repair:
        unscheduled, _ = evt._run_repair_pass(schedule, unscheduled, score_config, children_by_op)

    metrics = evt._evaluate_schedule_metrics(
        schedule, list(schedule.operations.values()), sites, start_date, end_date, score_config
    )
    recorder.record_run_summary(
        {
            "scheduled_operations": len(schedule.get_scheduled_operations()),
            "unscheduled_operations": len(unscheduled),
            "strategy_score": metrics["strategy_score"],
            "priority_weighted_coverage_percent": metrics["priority_weighted_coverage_percent"],
            "site_capacity_used_percent": metrics["site_capacity_used_percent"],
        }
    )
    recorder.close()
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Collect imitation-learning episodes.")
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--seed-base", type=int, default=None)
    parser.add_argument("--output-dir", default=DEFAULT_DATA_DIR)
    parser.add_argument("--scheduler-mode", default="enhanced_dispatch", choices=["priority", "enhanced_dispatch"])
    parser.add_argument("--skip-repair", action="store_true")
    args = parser.parse_args()

    out_paths = []
    for episode_idx in range(max(1, args.episodes)):
        seed = None if args.seed_base is None else int(args.seed_base) + episode_idx
        out_paths.append(
            _collect_one_episode(
                output_dir=args.output_dir,
                episode_idx=episode_idx,
                seed=seed,
                scheduler_mode=args.scheduler_mode,
                use_repair=not args.skip_repair,
            )
        )

    print(f"Saved {len(out_paths)} imitation episodes:")
    for out_path in out_paths:
        print(f"  {out_path}")


if __name__ == "__main__":
    main()

