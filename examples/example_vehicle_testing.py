"""
Example: vehicle emissions testing plant (constraints exploration).
"""

from datetime import datetime
from collections import defaultdict
import sys
import os

# Ensure repo root is on the path so "classes" imports work
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from vehicle_testing_model import build_vehicle_testing_problem


def compute_priority_ranks_naive(tests):
    """
    Assign a unique global rank to each test (1 = highest priority).
    Uses existing 1-5 priority as the primary driver, then deterministic tie-breakers.
    """
    ranked_tests = sorted(
        tests,
        key=lambda op: (
            op.metadata.get("priority", 5),
            op.duration,
            op.operation_id,
        ),
    )
    for rank, op in enumerate(ranked_tests, start=1):
        op.metadata["priority_rank"] = rank


def compute_priority_ranks_site_demand(tests):
    """
    Assign unique ranks using site-demand-weighted importance.

    Steps:
    - Convert bucket priority (1-5) into a base importance score.
    - Compute average importance demand per site.
    - Increase test score when it can run on fewer sites.
    """
    site_importance_values = defaultdict(list)
    test_sites = {}

    for op in tests:
        base_priority = op.metadata.get("priority", 5)
        base_importance = max(1.0, 6.0 - float(base_priority))

        possible_sites = []
        for req in op.resource_requirements:
            if req.get("resource_type") == "site":
                possible_sites = req.get("possible_resource_ids", [])
                break

        test_sites[op.operation_id] = possible_sites
        for site_id in possible_sites:
            site_importance_values[site_id].append(base_importance)

    site_avg_importance = {
        site_id: (sum(values) / len(values))
        for site_id, values in site_importance_values.items()
        if values
    }

    for op in tests:
        possible_sites = test_sites.get(op.operation_id, [])
        flexibility_count = len(possible_sites) if possible_sites else 1
        avg_site_demand = (
            sum(site_avg_importance.get(site_id, 0.0) for site_id in possible_sites) / flexibility_count
            if possible_sites
            else 0.0
        )
        flexibility_weight = 1.0 / flexibility_count
        weighted_priority_score = avg_site_demand * (1.0 + flexibility_weight)

        op.metadata["avg_site_importance"] = avg_site_demand
        op.metadata["site_options"] = flexibility_count
        op.metadata["priority_score"] = weighted_priority_score

    ranked_tests = sorted(
        tests,
        key=lambda op: (
            -op.metadata.get("priority_score", 0.0),
            op.metadata.get("priority", 5),
            op.duration,
            op.operation_id,
        ),
    )
    for rank, op in enumerate(ranked_tests, start=1):
        op.metadata["priority_rank"] = rank

    return site_avg_importance


def compute_priority_ranks_site_demand_with_precedence(tests, propagation_weight=0.85):
    """
    Assign unique ranks using site-demand + flexibility, then propagate urgency backward
    across precedence edges so critical descendants pull predecessors earlier.

    propagation_weight controls how much downstream urgency is inherited.
    """
    site_avg_importance = compute_priority_ranks_site_demand(tests)
    op_by_id = {op.operation_id: op for op in tests}

    for op in tests:
        op.metadata["base_priority_score"] = op.metadata.get("priority_score", 0.0)
        op.metadata["effective_priority_score"] = op.metadata["base_priority_score"]

    # Reverse edges: predecessor -> list of children
    children_by_op = defaultdict(list)
    for op in tests:
        for pred_id in op.precedence:
            if pred_id in op_by_id:
                children_by_op[pred_id].append(op.operation_id)

    # Fixed-point propagation in reverse topological spirit.
    # A predecessor gets lifted if it unlocks high-urgency descendants.
    for _ in range(len(tests)):
        changed = False
        for op in tests:
            child_scores = [
                op_by_id[child_id].metadata.get("effective_priority_score", 0.0)
                for child_id in children_by_op.get(op.operation_id, [])
            ]
            inherited = max(child_scores) if child_scores else 0.0
            new_effective = max(
                op.metadata["base_priority_score"],
                propagation_weight * inherited,
            )
            if abs(new_effective - op.metadata["effective_priority_score"]) > 1e-9:
                op.metadata["effective_priority_score"] = new_effective
                changed = True
        if not changed:
            break

    ranked_tests = sorted(
        tests,
        key=lambda op: (
            -op.metadata.get("effective_priority_score", 0.0),
            -op.metadata.get("base_priority_score", 0.0),
            op.metadata.get("priority", 5),
            op.duration,
            op.operation_id,
        ),
    )
    for rank, op in enumerate(ranked_tests, start=1):
        op.metadata["priority_rank"] = rank

    return site_avg_importance


def compute_priority_ranks_importance_throughput(
    tests,
    importance_weight=1.4,
    scarcity_weight=1.2,
    unlock_weight=0.45,
    short_test_bonus_weight=0.55,
):
    """
    Balance high-importance tests with throughput (getting many tests done).

    Score components:
    - base importance from existing 1-5 priority
    - scarcity bonus for tests with fewer site options
    - unlock bonus for tests that unblock many descendants
    - short test bonus (value density) to improve test count throughput
    """
    op_by_id = {op.operation_id: op for op in tests}
    children_by_op = defaultdict(list)
    site_demand_map = compute_priority_ranks_site_demand(tests)

    for op in tests:
        for pred_id in op.precedence:
            if pred_id in op_by_id:
                children_by_op[pred_id].append(op.operation_id)

    descendants_cache = {}

    def count_descendants(op_id):
        if op_id in descendants_cache:
            return descendants_cache[op_id]
        seen = set()
        stack = list(children_by_op.get(op_id, []))
        while stack:
            child_id = stack.pop()
            if child_id in seen:
                continue
            seen.add(child_id)
            stack.extend(children_by_op.get(child_id, []))
        descendants_cache[op_id] = len(seen)
        return descendants_cache[op_id]

    for op in tests:
        base_priority = float(op.metadata.get("priority", 5))
        base_importance = max(1.0, 6.0 - base_priority)
        site_options = max(1, int(op.metadata.get("site_options", 1)))
        scarcity_bonus = 1.0 / site_options
        unlocked_count = count_descendants(op.operation_id)
        duration_hours = max(op.duration / 3600.0, 0.25)
        short_test_bonus = 1.0 / duration_hours

        score = (
            importance_weight * base_importance
            + scarcity_weight * scarcity_bonus
            + unlock_weight * unlocked_count
            + short_test_bonus_weight * short_test_bonus
        )

        op.metadata["priority_score"] = score
        op.metadata["importance_throughput_score"] = score
        op.metadata["unlocked_descendants"] = unlocked_count

    ranked_tests = sorted(
        tests,
        key=lambda op: (
            -op.metadata.get("importance_throughput_score", 0.0),
            op.metadata.get("priority", 5),
            op.duration,
            op.operation_id,
        ),
    )
    for rank, op in enumerate(ranked_tests, start=1):
        op.metadata["priority_rank"] = rank

    return site_demand_map


def compute_priority_ranks_bottleneck_density(
    tests,
    bottleneck_weight=1.25,
    density_weight=1.0,
    scarcity_weight=0.9,
    precedence_weight=0.6,
):
    """
    Emphasize bottleneck resources and value density.

    Score components:
    - bottleneck pressure (avg site demand)
    - importance per hour (priority-derived density)
    - scarcity bonus for low-flexibility tests
    - precedence pressure from direct child importance
    """
    site_demand_map = compute_priority_ranks_site_demand(tests)
    op_by_id = {op.operation_id: op for op in tests}
    children_by_op = defaultdict(list)

    for op in tests:
        for pred_id in op.precedence:
            if pred_id in op_by_id:
                children_by_op[pred_id].append(op.operation_id)

    for op in tests:
        base_priority = float(op.metadata.get("priority", 5))
        base_importance = max(1.0, 6.0 - base_priority)
        duration_hours = max(op.duration / 3600.0, 0.25)
        density = base_importance / duration_hours

        site_options = max(1, int(op.metadata.get("site_options", 1)))
        scarcity_bonus = 1.0 / site_options
        bottleneck_pressure = float(op.metadata.get("avg_site_importance", 0.0))

        direct_children = children_by_op.get(op.operation_id, [])
        if direct_children:
            child_pressures = [
                max(1.0, 6.0 - float(op_by_id[child_id].metadata.get("priority", 5)))
                for child_id in direct_children
            ]
            precedence_pressure = max(child_pressures)
        else:
            precedence_pressure = 0.0

        score = (
            bottleneck_weight * bottleneck_pressure
            + density_weight * density
            + scarcity_weight * scarcity_bonus
            + precedence_weight * precedence_pressure
        )

        op.metadata["priority_score"] = score
        op.metadata["bottleneck_density_score"] = score
        op.metadata["precedence_pressure"] = precedence_pressure

    ranked_tests = sorted(
        tests,
        key=lambda op: (
            -op.metadata.get("bottleneck_density_score", 0.0),
            op.metadata.get("priority", 5),
            op.duration,
            op.operation_id,
        ),
    )
    for rank, op in enumerate(ranked_tests, start=1):
        op.metadata["priority_rank"] = rank

    return site_demand_map


def main():
    schedule, tests, sites, vehicles, start_date, end_date = build_vehicle_testing_problem()

    ranking_strategies = {
        "naive": lambda ops: (compute_priority_ranks_naive(ops) or {}),
        "site_demand": lambda ops: compute_priority_ranks_site_demand(ops),
        "site_demand_with_precedence": lambda ops: compute_priority_ranks_site_demand_with_precedence(
            ops, propagation_weight=0.85
        ),
        "importance_throughput": lambda ops: compute_priority_ranks_importance_throughput(
            ops,
            importance_weight=1.4,
            scarcity_weight=1.2,
            unlock_weight=0.45,
            short_test_bonus_weight=0.55,
        ),
        "bottleneck_density": lambda ops: compute_priority_ranks_bottleneck_density(
            ops,
            bottleneck_weight=1.25,
            density_weight=1.0,
            scarcity_weight=0.9,
            precedence_weight=0.6,
        ),
    }
    strategies_to_compare = list(ranking_strategies.keys())

    def run_greedy_schedule():
        unscheduled = [op for op in schedule.operations.values()]
        unscheduled_tests = []
        while unscheduled:
            ready = [
                op for op in unscheduled
                if all(schedule.operations[p].is_scheduled() for p in op.precedence)
            ]
            if not ready:
                break
            ready.sort(key=lambda op: op.metadata.get("priority_rank", 10**9))

            selected = ready[0]
            earliest = start_date.timestamp()
            if selected.precedence:
                earliest = max(
                    earliest,
                    max(schedule.operations[p].end_time for p in selected.precedence),
                )
            if not selected.can_start_at(earliest, schedule.operations):
                unscheduled.remove(selected)
                unscheduled_tests.append(selected)
                continue
            try:
                start_ts, assigned = schedule._find_earliest_slot_any_resource(selected, earliest)
            except RuntimeError:
                unscheduled.remove(selected)
                unscheduled_tests.append(selected)
                continue

            if start_ts + selected.duration > end_date.timestamp():
                unscheduled.remove(selected)
                unscheduled_tests.append(selected)
                continue

            if schedule.schedule_operation_multi(
                selected.operation_id, assigned, datetime.fromtimestamp(start_ts)
            ):
                unscheduled.remove(selected)
            else:
                unscheduled.remove(selected)
                unscheduled_tests.append(selected)

        for op in list(unscheduled):
            unscheduled_tests.append(op)
            unscheduled.remove(op)
        return unscheduled_tests

    def get_avg_site_utilization():
        start_ts = start_date.timestamp()
        end_ts = end_date.timestamp()
        site_utils = [
            resource.get_utilization(start_ts, end_ts)
            for resource in schedule.resources.values()
            if resource.resource_type == "site"
        ]
        return sum(site_utils) / len(site_utils) if site_utils else 0.0

    planning_window_seconds = (end_date - start_date).total_seconds()
    site_capacity_seconds = len(sites) * planning_window_seconds
    total_demand_seconds = sum(op.duration for op in tests)
    # =========================
    # Schedule scoring settings
    # =========================
    # Keep these together so future tuning/range-sweeps are easy.
    SCORE_CONFIG = {
        # Strong separation at top priorities.
        "priority_bucket_weights": {
            1: 30.0, 
            2: 15.0, 
            3: 6.0, 
            4: 2.0, 
            5: 1.0
        },
        # Duration exponent (<1 favors throughput of shorter tests).
        "duration_exponent_gamma": 0.6,
        # Overall objective mix.
        "priority_coverage_weight": 0.80,
        "site_utilization_weight": 0.20,
    }

    def get_priority_weight(op, priority_bucket_weights):
        priority_bucket = int(op.metadata.get("priority", 5))
        return priority_bucket_weights.get(priority_bucket, 1.0)

    def get_weighted_test_value_seconds(op, config):
        hours = max(op.duration / 3600.0, 0.0)
        priority_weight = get_priority_weight(op, config["priority_bucket_weights"])
        value_in_hour_units = priority_weight * (hours ** config["duration_exponent_gamma"])
        # Keep a seconds-like scale for easier intuition in aggregates.
        return value_in_hour_units * 3600.0

    total_priority_weighted_value = sum(
        get_weighted_test_value_seconds(op, SCORE_CONFIG) for op in tests
    )
    comparison_results = []

    for strategy_name in strategies_to_compare:
        schedule.clear_all_schedules()
        site_demand_map = ranking_strategies[strategy_name](tests)
        unscheduled_tests = run_greedy_schedule()
        stats = schedule.get_schedule_statistics()
        scheduled_ops = schedule.get_scheduled_operations()
        scheduled_seconds = sum(op.duration for op in scheduled_ops.values())
        scheduled_priority_weighted_value = sum(
            get_weighted_test_value_seconds(op, SCORE_CONFIG) for op in scheduled_ops.values()
        )
        unscheduled_seconds = total_demand_seconds - scheduled_seconds
        avg_site_utilization = get_avg_site_utilization()
        demand_coverage_percent = (
            (scheduled_seconds / total_demand_seconds) * 100 if total_demand_seconds > 0 else 0.0
        )
        priority_weighted_coverage_percent = (
            (scheduled_priority_weighted_value / total_priority_weighted_value) * 100
            if total_priority_weighted_value > 0
            else 0.0
        )
        site_capacity_used_percent = (
            (scheduled_seconds / site_capacity_seconds) * 100 if site_capacity_seconds > 0 else 0.0
        )
        strategy_score = (
            SCORE_CONFIG["priority_coverage_weight"] * (priority_weighted_coverage_percent / 100.0)
            + SCORE_CONFIG["site_utilization_weight"] * (site_capacity_used_percent / 100.0)
        )
        comparison_results.append(
            {
                "strategy": strategy_name,
                "scheduled_operations": len(scheduled_ops),
                "unscheduled_operations": len(unscheduled_tests),
                "scheduled_seconds": scheduled_seconds,
                "scheduled_priority_weighted_value": scheduled_priority_weighted_value,
                "unscheduled_seconds": unscheduled_seconds,
                "demand_coverage_percent": demand_coverage_percent,
                "priority_weighted_coverage_percent": priority_weighted_coverage_percent,
                "site_capacity_used_percent": site_capacity_used_percent,
                "strategy_score": strategy_score,
                "makespan_hours": stats["makespan_hours"],
                "avg_site_utilization": avg_site_utilization,
                "site_demand_map": site_demand_map,
            }
        )

    print("\n=== Strategy Comparison ===")
    for result in comparison_results:
        print(
            f"  {result['strategy']}: "
            f"{result['scheduled_operations']} scheduled, "
            f"{result['unscheduled_operations']} unscheduled, "
            f"unscheduled workload {result['unscheduled_seconds'] / 3600:.2f}h, "
            f"priority coverage {result['priority_weighted_coverage_percent']:.1f}%, "
            f"makespan {result['makespan_hours']:.2f}h, "
            f"site capacity used {result['site_capacity_used_percent'] / 100:.1%}, "
            f"site utilization {result['avg_site_utilization']:.1%}, "
            f"weighted score {result['strategy_score']:.4f}"
        )

    best_result = max(
        comparison_results,
        key=lambda r: r["strategy_score"],
    )
    best_strategy = best_result["strategy"]

    # Re-run the winner so gantt charts and detail metrics reflect the best schedule.
    schedule.clear_all_schedules()
    site_demand_map = ranking_strategies[best_strategy](tests)
    unscheduled_tests = run_greedy_schedule()

    stats = schedule.get_schedule_statistics()
    scheduled_seconds = sum(op.duration for op in schedule.get_scheduled_operations().values())
    scheduled_priority_weighted_value = sum(
        get_weighted_test_value_seconds(op, SCORE_CONFIG)
        for op in schedule.get_scheduled_operations().values()
    )
    unscheduled_seconds = total_demand_seconds - scheduled_seconds
    demand_coverage_percent = (
        (scheduled_seconds / total_demand_seconds) * 100 if total_demand_seconds > 0 else 0.0
    )
    priority_weighted_coverage_percent = (
        (scheduled_priority_weighted_value / total_priority_weighted_value) * 100
        if total_priority_weighted_value > 0
        else 0.0
    )
    site_capacity_used_percent = (
        (scheduled_seconds / site_capacity_seconds) * 100 if site_capacity_seconds > 0 else 0.0
    )
    avg_site_utilization = get_avg_site_utilization()
    selected_strategy_score = (
        SCORE_CONFIG["priority_coverage_weight"] * (priority_weighted_coverage_percent / 100.0)
        + SCORE_CONFIG["site_utilization_weight"] * (site_capacity_used_percent / 100.0)
    )

    print("\n=== Selected Best Strategy ===")
    print(f"  {best_strategy}")
    print(f"  Scheduled operations: {len(schedule.get_scheduled_operations())}")
    print("\nSchedule quality metrics:")
    print(f"  Priority strategy: {best_strategy}")
    print(
        f"  Weighted strategy score: {selected_strategy_score:.4f} "
        f"(priority coverage {SCORE_CONFIG['priority_coverage_weight']:.0%} + "
        f"site time {SCORE_CONFIG['site_utilization_weight']:.0%})"
    )
    print(
        f"  Scoring params: gamma={SCORE_CONFIG['duration_exponent_gamma']}, "
        f"bucket_weights={SCORE_CONFIG['priority_bucket_weights']}"
    )
    print(f"  Scheduled workload (site-hours): {scheduled_seconds / 3600:.2f}h")
    print(f"  Site capacity window: {site_capacity_seconds / 3600:.2f}h ({len(sites)} sites x {(planning_window_seconds / 3600):.0f}h)")
    print(f"  Site capacity used: {site_capacity_used_percent:.1f}%")
    print(f"  Priority-weighted coverage: {priority_weighted_coverage_percent:.1f}%")
    print(f"  Demand covered: {scheduled_seconds / 3600:.2f}h / {total_demand_seconds / 3600:.2f}h ({demand_coverage_percent:.1f}%)")
    print(f"  Unscheduled workload time: {unscheduled_seconds / 3600:.2f}h")
    print(f"  Makespan: {stats['makespan_hours']:.2f}h")
    print(f"  Avg utilization (sites only): {avg_site_utilization:.1%}")
    print("\nAvg site importance demand:")
    for site_id in sorted(site_demand_map):
        print(f"  {site_id}: {site_demand_map[site_id]:.2f}")

    if unscheduled_tests:
        print("\nUnscheduled tests:")
        for op in unscheduled_tests:
            print(
                f"  {op.operation_id} "
                f"(rank {op.metadata.get('priority_rank')}, priority {op.metadata.get('priority', 5)})"
            )

    schedule.create_gantt_chart()
    schedule.show_visual_gantt_chart(resource_type_filter=["site"], title_suffix="Sites", block=False)
    schedule.show_visual_gantt_chart(resource_type_filter=["vehicle"], title_suffix="Vehicles", block=True)

    print("Vehicle testing scenario constructed.")


if __name__ == "__main__":
    main()
