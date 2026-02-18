"""
Example: vehicle emissions testing plant (constraints exploration).
"""

from datetime import datetime
from collections import defaultdict
from copy import deepcopy
import itertools
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


def _build_children_map(tests):
    children_by_op = defaultdict(list)
    for op in tests:
        for pred_id in op.precedence:
            children_by_op[pred_id].append(op.operation_id)
    return children_by_op


def _build_descendant_counts(children_by_op):
    counts = {}
    all_ids = set(children_by_op.keys())
    for children in children_by_op.values():
        all_ids.update(children)

    for op_id in all_ids:
        seen = set()
        stack = list(children_by_op.get(op_id, []))
        while stack:
            child = stack.pop()
            if child in seen:
                continue
            seen.add(child)
            stack.extend(children_by_op.get(child, []))
        counts[op_id] = len(seen)
    return counts


def _get_priority_weight(op, priority_bucket_weights):
    priority_bucket = int(op.metadata.get("priority", 5))
    return priority_bucket_weights.get(priority_bucket, 1.0)


def _get_weighted_test_value_seconds(op, config, duration_seconds_override=None):
    duration_seconds = duration_seconds_override if duration_seconds_override is not None else op.duration
    hours = max(duration_seconds / 3600.0, 0.0)
    priority_weight = _get_priority_weight(op, config["priority_bucket_weights"])
    value_in_hour_units = priority_weight * (hours ** config["duration_exponent_gamma"])
    return value_in_hour_units * 3600.0


def _evaluate_schedule_metrics(schedule, tests, sites, start_date, end_date, score_config):
    planning_window_seconds = (end_date - start_date).total_seconds()
    site_capacity_seconds = len(sites) * planning_window_seconds
    total_demand_seconds = sum(op.duration for op in tests)

    scheduled_ops = schedule.get_scheduled_operations()
    scheduled_seconds = sum((op.end_time - op.start_time) for op in scheduled_ops.values())
    unscheduled_seconds = total_demand_seconds - scheduled_seconds

    total_priority_weighted_value = sum(
        _get_weighted_test_value_seconds(op, score_config) for op in tests
    )
    scheduled_priority_weighted_value = sum(
        _get_weighted_test_value_seconds(
            op, score_config, duration_seconds_override=(op.end_time - op.start_time)
        )
        for op in scheduled_ops.values()
    )

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

    start_ts = start_date.timestamp()
    end_ts = end_date.timestamp()
    site_utils = [
        resource.get_utilization(start_ts, end_ts)
        for resource in schedule.resources.values()
        if resource.resource_type == "site"
    ]
    avg_site_utilization = sum(site_utils) / len(site_utils) if site_utils else 0.0

    strategy_score = (
        score_config["priority_coverage_weight"] * (priority_weighted_coverage_percent / 100.0)
        + score_config["site_utilization_weight"] * (site_capacity_used_percent / 100.0)
    )

    return {
        "planning_window_seconds": planning_window_seconds,
        "site_capacity_seconds": site_capacity_seconds,
        "total_demand_seconds": total_demand_seconds,
        "scheduled_seconds": scheduled_seconds,
        "unscheduled_seconds": unscheduled_seconds,
        "demand_coverage_percent": demand_coverage_percent,
        "priority_weighted_coverage_percent": priority_weighted_coverage_percent,
        "site_capacity_used_percent": site_capacity_used_percent,
        "avg_site_utilization": avg_site_utilization,
        "strategy_score": strategy_score,
    }


def _score_ready_candidate(
    schedule,
    operation,
    start_date,
    end_date,
    descendant_counts,
    mode,
):
    earliest = start_date.timestamp()
    if operation.precedence:
        earliest = max(earliest, max(schedule.operations[p].end_time for p in operation.precedence))
    if not operation.can_start_at(earliest, schedule.operations):
        return None

    try:
        start_ts, assigned = schedule._find_earliest_slot_any_resource(operation, earliest)
    except RuntimeError:
        return None

    effective_duration = schedule.get_effective_duration_for_assignment(
        operation.operation_id, assigned
    )
    finish_ts = start_ts + effective_duration
    if finish_ts > end_date.timestamp():
        return None

    if mode == "priority":
        return {
            "score": -(operation.metadata.get("priority_rank", 10**9)),
            "start_ts": start_ts,
            "assigned": assigned,
        }

    rank = operation.metadata.get("priority_rank", 10**9)
    priority_term = 1.0 / (1.0 + rank)
    slack_hours = max(0.0, (end_date.timestamp() - finish_ts) / 3600.0)
    slack_urgency_term = 1.0 / (1.0 + slack_hours)
    throughput_term = 1.0 / max(effective_duration / 3600.0, 0.25)
    bottleneck_term = float(operation.metadata.get("avg_site_importance", 0.0)) / 6.0
    max_desc = max(descendant_counts.values()) if descendant_counts else 1
    unlock_term = descendant_counts.get(operation.operation_id, 0) / max(max_desc, 1)

    score = (
        0.50 * priority_term
        + 0.20 * slack_urgency_term
        + 0.15 * throughput_term
        + 0.10 * bottleneck_term
        + 0.05 * unlock_term
    )
    return {
        "score": score,
        "start_ts": start_ts,
        "assigned": assigned,
    }


def _run_greedy_schedule(
    schedule,
    start_date,
    end_date,
    descendant_counts,
    mode="priority",
    max_ready_eval=None,
    max_runtime_seconds=None,
):
    start_perf = datetime.now().timestamp()
    unscheduled = [op for op in schedule.operations.values()]
    unscheduled_tests = []

    while unscheduled:
        if max_runtime_seconds is not None:
            if datetime.now().timestamp() - start_perf > max_runtime_seconds:
                unscheduled_tests.extend(unscheduled)
                break
        ready = [
            op for op in unscheduled
            if all(schedule.operations[p].is_scheduled() for p in op.precedence)
        ]
        if not ready:
            break

        if max_ready_eval is not None and len(ready) > max_ready_eval:
            # Cheap pre-filter before expensive feasibility probing.
            if mode == "enhanced_dispatch":
                ready = sorted(
                    ready,
                    key=lambda op: (
                        op.metadata.get("priority_rank", 10**9),
                        -op.metadata.get("avg_site_importance", 0.0),
                        op.duration,
                        op.operation_id,
                    ),
                )[:max_ready_eval]
            else:
                ready = sorted(
                    ready,
                    key=lambda op: (
                        op.metadata.get("priority_rank", 10**9),
                        op.duration,
                        op.operation_id,
                    ),
                )[:max_ready_eval]

        best = None
        selected = None
        for op in ready:
            candidate = _score_ready_candidate(
                schedule, op, start_date, end_date, descendant_counts, mode
            )
            if candidate is None:
                continue
            if best is None or candidate["score"] > best["score"]:
                best = candidate
                selected = op

        if selected is None:
            break

        if schedule.schedule_operation_multi(
            selected.operation_id, best["assigned"], datetime.fromtimestamp(best["start_ts"])
        ):
            unscheduled.remove(selected)
        else:
            unscheduled.remove(selected)
            unscheduled_tests.append(selected)

    for op in list(unscheduled):
        unscheduled_tests.append(op)
        unscheduled.remove(op)
    return unscheduled_tests


def _run_repair_pass(
    schedule,
    unscheduled_tests,
    score_config,
    children_by_op,
    max_candidates=24,
    max_assignments_per_candidate=24,
    max_starts_per_assignment=40,
    max_runtime_seconds=None,
):
    """
    Lightweight repair pass: place high-value unscheduled operations by evicting
    at most one lower-value conflicting leaf operation.
    """
    unscheduled_set = {op.operation_id for op in unscheduled_tests}
    made_change = False
    repair_start_perf = datetime.now().timestamp()

    ranked_unscheduled = sorted(
        unscheduled_tests,
        key=lambda op: _get_weighted_test_value_seconds(op, score_config),
        reverse=True,
    )
    for candidate in ranked_unscheduled[:max_candidates]:
        if max_runtime_seconds is not None:
            if datetime.now().timestamp() - repair_start_perf > max_runtime_seconds:
                break
        if any(
            (pred_id in unscheduled_set) or (not schedule.operations[pred_id].is_scheduled())
            for pred_id in candidate.precedence
        ):
            continue

        requirements = candidate.get_resource_requirements()
        if not requirements:
            continue
        resource_candidates = [req["possible_resource_ids"] for req in requirements]

        earliest = schedule.start_date.timestamp()
        if candidate.precedence:
            earliest = max(
                earliest, max(schedule.operations[p].end_time for p in candidate.precedence)
            )

        for assignment_idx, assignment in enumerate(itertools.product(*resource_candidates)):
            if max_runtime_seconds is not None:
                if datetime.now().timestamp() - repair_start_perf > max_runtime_seconds:
                    break
            if assignment_idx >= max_assignments_per_candidate:
                break
            assigned_resources = schedule._build_assigned_resources(requirements, list(assignment))
            duration = schedule.get_effective_duration_for_assignment(
                candidate.operation_id, assigned_resources
            )

            candidate_starts = {earliest}
            for resource_id in assignment:
                for op in schedule.resources[resource_id].schedule:
                    if op.end_time >= earliest:
                        candidate_starts.add(op.end_time)

            for start_idx, start_ts in enumerate(sorted(candidate_starts)):
                if start_idx >= max_starts_per_assignment:
                    break
                end_ts = start_ts + duration
                if end_ts > schedule.end_date.timestamp():
                    continue

                conflicting_ops = set()
                feasible = True
                for req, resource_id in zip(requirements, assignment):
                    resource = schedule.resources.get(resource_id)
                    if not resource:
                        feasible = False
                        break
                    for op in resource.schedule:
                        if op.end_time <= start_ts or op.start_time >= end_ts:
                            continue
                        conflicting_ops.add(op)
                    if not schedule._constraints_allow(candidate, resource, start_ts, end_ts):
                        feasible = False
                        break
                if not feasible:
                    continue

                if len(conflicting_ops) > 1:
                    continue

                evicted_op = next(iter(conflicting_ops), None)
                if evicted_op is not None:
                    if children_by_op.get(evicted_op.operation_id):
                        continue
                    candidate_value = _get_weighted_test_value_seconds(candidate, score_config)
                    evicted_value = _get_weighted_test_value_seconds(evicted_op, score_config)
                    if candidate_value <= evicted_value:
                        continue
                    evicted_start_ts = evicted_op.start_time
                    evicted_assigned = dict(evicted_op.assigned_resources)
                    schedule.unschedule_operation(evicted_op.operation_id)
                    unscheduled_set.add(evicted_op.operation_id)
                    unscheduled_tests.append(evicted_op)

                if not candidate.can_start_at(start_ts, schedule.operations):
                    continue

                placed = schedule.schedule_operation_multi(
                    candidate.operation_id,
                    assigned_resources,
                    datetime.fromtimestamp(start_ts),
                )
                if not placed:
                    if evicted_op is not None:
                        schedule.schedule_operation_multi(
                            evicted_op.operation_id,
                            evicted_assigned,
                            datetime.fromtimestamp(evicted_start_ts),
                        )
                        unscheduled_set.discard(evicted_op.operation_id)
                        unscheduled_tests = [
                            op for op in unscheduled_tests if op.operation_id != evicted_op.operation_id
                        ]
                    continue

                unscheduled_set.discard(candidate.operation_id)
                unscheduled_tests = [
                    op for op in unscheduled_tests if op.operation_id != candidate.operation_id
                ]
                made_change = True
                break

            if candidate.operation_id not in unscheduled_set:
                break

    return unscheduled_tests, made_change


def main():
    schedule, tests, sites, vehicles, start_date, end_date = build_vehicle_testing_problem()

    ranking_strategies = {
        "naive": lambda ops: (compute_priority_ranks_naive(ops) or {}),
        # "site_demand": lambda ops: compute_priority_ranks_site_demand(ops),
        # "site_demand_with_precedence": lambda ops: compute_priority_ranks_site_demand_with_precedence(
        #     ops, propagation_weight=0.85
        # ),
        # "importance_throughput": lambda ops: compute_priority_ranks_importance_throughput(
        #     ops,
        #     importance_weight=1.4,
        #     scarcity_weight=1.2,
        #     unlock_weight=0.45,
        #     short_test_bonus_weight=0.55,
        # ),
        # "bottleneck_density": lambda ops: compute_priority_ranks_bottleneck_density(
        #     ops,
        #     bottleneck_weight=1.25,
        #     density_weight=1.0,
        #     scarcity_weight=0.9,
        #     precedence_weight=0.6,
        # ),
    }
    strategies_to_compare = list(ranking_strategies.keys())

    children_by_op = _build_children_map(tests)
    descendant_counts = _build_descendant_counts(children_by_op)
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
    PERFORMANCE_CONFIG = {
        # Bound expensive ready-candidate feasibility scoring per iteration.
        "max_ready_eval": 24,
        # Keep runtime cutoffs disabled by default to avoid truncating schedules.
        "max_greedy_runtime_seconds": None,
        "max_repair_runtime_seconds": None,
        # Bound repair search effort.
        "max_repair_candidates": 24,
        "max_repair_assignments_per_candidate": 16,
        "max_repair_starts_per_assignment": 24,
    }

    comparison_results = []
    scheduler_modes = {
        "priority_greedy": {"base_mode": "priority", "repair": False},
        # "enhanced_dispatch_repair": {"base_mode": "enhanced_dispatch", "repair": True},
    }

    # For each ranking strategy, run the scheduler modes and compare the results.
    for strategy_name in strategies_to_compare:
        ranked_schedule = deepcopy(schedule)
        ranked_tests = list(ranked_schedule.operations.values())
        site_demand_map = ranking_strategies[strategy_name](ranked_tests)

        # For each scheduler mode
        for scheduler_name, scheduler_cfg in scheduler_modes.items():
            run_schedule = deepcopy(ranked_schedule)

            if scheduler_cfg["base_mode"] == "priority":
                unscheduled_tests = _run_greedy_schedule(
                    run_schedule,
                    start_date,
                    end_date,
                    descendant_counts,
                    mode="priority",
                    max_ready_eval=PERFORMANCE_CONFIG["max_ready_eval"],
                    max_runtime_seconds=PERFORMANCE_CONFIG["max_greedy_runtime_seconds"],
                )
            elif scheduler_cfg["base_mode"] == "enhanced_dispatch":
                unscheduled_tests = _run_greedy_schedule(
                    run_schedule,
                    start_date,
                    end_date,
                    descendant_counts,
                    mode="enhanced_dispatch",
                    max_ready_eval=PERFORMANCE_CONFIG["max_ready_eval"],
                    max_runtime_seconds=PERFORMANCE_CONFIG["max_greedy_runtime_seconds"],
                )
            else:
                raise ValueError(f"Unknown scheduler mode: {scheduler_cfg['base_mode']}")

            if scheduler_cfg["repair"]:
                unscheduled_tests, _ = _run_repair_pass(
                    run_schedule,
                    unscheduled_tests,
                    SCORE_CONFIG,
                    children_by_op,
                    max_candidates=PERFORMANCE_CONFIG["max_repair_candidates"],
                    max_assignments_per_candidate=PERFORMANCE_CONFIG["max_repair_assignments_per_candidate"],
                    max_starts_per_assignment=PERFORMANCE_CONFIG["max_repair_starts_per_assignment"],
                    max_runtime_seconds=PERFORMANCE_CONFIG["max_repair_runtime_seconds"],
                )

            stats = run_schedule.get_schedule_statistics()
            run_metrics = _evaluate_schedule_metrics(
                run_schedule, list(run_schedule.operations.values()), sites, start_date, end_date, SCORE_CONFIG
            )
            scheduled_ops = run_schedule.get_scheduled_operations()
            comparison_results.append(
                {
                    "ranking_strategy": strategy_name,
                    "scheduler": scheduler_name,
                    "scheduled_operations": len(scheduled_ops),
                    "unscheduled_operations": len(unscheduled_tests),
                    "scheduled_seconds": run_metrics["scheduled_seconds"],
                    "unscheduled_seconds": run_metrics["unscheduled_seconds"],
                    "demand_coverage_percent": run_metrics["demand_coverage_percent"],
                    "priority_weighted_coverage_percent": run_metrics["priority_weighted_coverage_percent"],
                    "site_capacity_used_percent": run_metrics["site_capacity_used_percent"],
                    "strategy_score": run_metrics["strategy_score"],
                    "makespan_hours": stats["makespan_hours"],
                    "avg_site_utilization": run_metrics["avg_site_utilization"],
                    "site_demand_map": site_demand_map,
                    "schedule_snapshot": run_schedule,
                }
            )

    print("\n=== Strategy x Scheduler Comparison ===")
    for result in comparison_results:
        print(
            f"  {result['ranking_strategy']} | {result['scheduler']}: "
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
    best_strategy = best_result["ranking_strategy"]
    best_scheduler = best_result["scheduler"]
    schedule = best_result["schedule_snapshot"]
    site_demand_map = best_result["site_demand_map"]
    unscheduled_tests = [op for op in schedule.operations.values() if not op.is_scheduled()]
    stats = schedule.get_schedule_statistics()
    run_metrics = _evaluate_schedule_metrics(
        schedule, list(schedule.operations.values()), sites, start_date, end_date, SCORE_CONFIG
    )

    print("\n=== Selected Best Strategy ===")
    print(f"  Ranking strategy: {best_strategy}")
    print(f"  Scheduler mode: {best_scheduler}")
    print(f"  Scheduled operations: {len(schedule.get_scheduled_operations())}")
    print("\nSchedule quality metrics:")
    print(f"  Priority strategy: {best_strategy}")
    print(
        f"  Weighted strategy score: {run_metrics['strategy_score']:.4f} "
        f"(priority coverage {SCORE_CONFIG['priority_coverage_weight']:.0%} + "
        f"site time {SCORE_CONFIG['site_utilization_weight']:.0%})"
    )
    print(
        f"  Scoring params: gamma={SCORE_CONFIG['duration_exponent_gamma']}, "
        f"bucket_weights={SCORE_CONFIG['priority_bucket_weights']}"
    )
    print(f"  Scheduled workload (site-hours): {run_metrics['scheduled_seconds'] / 3600:.2f}h")
    print(
        f"  Site capacity window: {run_metrics['site_capacity_seconds'] / 3600:.2f}h "
        f"({len(sites)} sites x {(run_metrics['planning_window_seconds'] / 3600):.0f}h)"
    )
    print(f"  Site capacity used: {run_metrics['site_capacity_used_percent']:.1f}%")
    print(f"  Priority-weighted coverage: {run_metrics['priority_weighted_coverage_percent']:.1f}%")
    print(
        f"  Demand covered: {run_metrics['scheduled_seconds'] / 3600:.2f}h / "
        f"{run_metrics['total_demand_seconds'] / 3600:.2f}h "
        f"({run_metrics['demand_coverage_percent']:.1f}%)"
    )
    print(f"  Unscheduled workload time: {run_metrics['unscheduled_seconds'] / 3600:.2f}h")
    print(f"  Makespan: {stats['makespan_hours']:.2f}h")
    print(f"  Avg utilization (sites only): {run_metrics['avg_site_utilization']:.1%}")
    print("\nAvg site importance demand:")
    for site_id in sorted(site_demand_map):
        print(f"  {site_id}: {site_demand_map[site_id]:.2f}")

    print("\nAdoption criteria:")
    print("  - Keep enhanced greedy+repair when score delta vs baseline is small (<3%).")
    print("  - Keep enhanced dispatch+repair when medium score gains are stable.")

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
