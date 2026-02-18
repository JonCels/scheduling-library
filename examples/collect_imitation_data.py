"""
Generate imitation-learning trajectory data from heuristic scheduling.
"""

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


def main():
    schedule, tests, sites, _vehicles, start_date, end_date = build_vehicle_testing_problem()
    children_by_op = evt._build_children_map(tests)
    descendant_counts = evt._build_descendant_counts(children_by_op)
    evt.compute_priority_ranks_naive(tests)

    data_dir = DEFAULT_DATA_DIR
    os.makedirs(data_dir, exist_ok=True)
    out_path = os.path.join(
        data_dir, f"episode_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jsonl"
    )

    recorder = TrajectoryRecorder(
        output_path=out_path,
        run_metadata={
            "ranking_strategy": "naive",
            "scheduler_mode": "enhanced_dispatch_repair",
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
        mode="enhanced_dispatch",
        decision_callback=decision_callback,
    )
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

    print(f"Saved imitation episode: {out_path}")


if __name__ == "__main__":
    main()

