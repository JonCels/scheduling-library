"""
Utilities for generating randomized vehicle-test samples.

The hardcoded tests in vehicle_testing_model.py are used as seed templates, then we:
1) build a larger synthetic pool (default 500 tests),
2) sample a random subset for scheduling runs (default 120 tests),
3) add sparse precedence links only within the sampled subset.
"""

from __future__ import annotations

import random
from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Sequence

from classes.operation import Operation


def _weighted_choice(rng: random.Random, items: Sequence[str], weights: Sequence[float]) -> str:
    return rng.choices(items, weights=weights, k=1)[0]


def _weighted_unique_sample(
    rng: random.Random,
    items: Sequence[str],
    weights: Sequence[float],
    k: int,
) -> List[str]:
    """Sample k unique items using weighted draws without replacement."""
    k = max(1, min(k, len(items)))
    pool_items = list(items)
    pool_weights = list(weights)
    selected: List[str] = []
    for _ in range(k):
        choice = _weighted_choice(rng, pool_items, pool_weights)
        idx = pool_items.index(choice)
        selected.append(choice)
        pool_items.pop(idx)
        pool_weights.pop(idx)
        if not pool_items:
            break
    return selected


def _extract_resource_ids(base_tests: Iterable[Operation], resource_type: str) -> List[str]:
    values = set()
    for op in base_tests:
        for req in op.get_resource_requirements():
            if req.get("resource_type") == resource_type:
                values.update(req.get("possible_resource_ids", []))
    return sorted(values)


def _extract_site_count_distribution() -> Dict[int, float]:
    # Requested shape: spikes around 1, 2, 3, and 5 options.
    return {
        1: 0.24,
        2: 0.26,
        3: 0.22,
        4: 0.05,
        5: 0.15,
        6: 0.03,
        7: 0.02,
        8: 0.015,
        9: 0.01,
        10: 0.005,
    }


def _get_site_weights(base_tests: Sequence[Operation], site_ids: Sequence[str]) -> List[float]:
    counts = {site_id: 1.0 for site_id in site_ids}
    for op in base_tests:
        for req in op.get_resource_requirements():
            if req.get("resource_type") != "site":
                continue
            for site_id in req.get("possible_resource_ids", []):
                if site_id in counts:
                    counts[site_id] += 1.0
    return [counts[site_id] for site_id in site_ids]


def _get_vehicle_weights(base_tests: Sequence[Operation], vehicle_ids: Sequence[str], rng: random.Random) -> List[float]:
    counts = defaultdict(float)
    for op in base_tests:
        counts[op.job_id] += 1.0

    # Make a few vehicles "hot" so repeats happen naturally.
    hot_vehicle_count = max(1, len(vehicle_ids) // 6)
    hot_vehicles = set(rng.sample(list(vehicle_ids), k=hot_vehicle_count))

    weights: List[float] = []
    for vehicle_id in vehicle_ids:
        w = counts.get(vehicle_id, 1.0)
        if vehicle_id in hot_vehicles:
            w *= rng.uniform(1.6, 3.0)
        weights.append(w)
    return weights


def _round_to_quarter_hour(seconds: float) -> float:
    quarter = 15 * 60
    rounded = round(seconds / quarter) * quarter
    return float(max(0.75 * 3600, min(3.5 * 3600, rounded)))


def generate_random_test_pool(
    base_tests: Sequence[Operation],
    pool_size: int = 500,
    seed: Optional[int] = None,
) -> List[Operation]:
    """
    Generate a synthetic test pool based on hardcoded tests.
    """
    if not base_tests:
        return []

    rng = random.Random(seed)
    site_ids = _extract_resource_ids(base_tests, "site") or [f"Site_{i}" for i in range(1, 11)]
    vehicle_ids = _extract_resource_ids(base_tests, "vehicle") or [f"VEHICLE_{i:03d}" for i in range(1, 51)]
    site_weights = _get_site_weights(base_tests, site_ids)
    vehicle_weights = _get_vehicle_weights(base_tests, vehicle_ids, rng)

    site_count_dist = _extract_site_count_distribution()
    site_count_values = list(site_count_dist.keys())
    site_count_weights = list(site_count_dist.values())

    width = max(3, len(str(pool_size)))
    synthetic_ops: List[Operation] = []

    for idx in range(1, pool_size + 1):
        template = rng.choice(base_tests)
        vehicle_id = _weighted_choice(rng, vehicle_ids, vehicle_weights)

        requested_site_count = rng.choices(site_count_values, weights=site_count_weights, k=1)[0]
        site_count = max(1, min(len(site_ids), requested_site_count))
        site_options = _weighted_unique_sample(rng, site_ids, site_weights, site_count)

        duration_jitter = rng.uniform(0.85, 1.20)
        duration = _round_to_quarter_hour(float(template.duration) * duration_jitter)

        test_type = template.metadata.get("test_type", rng.choice(["A", "B", "C", "D", "E"]))
        base_priority = int(template.metadata.get("priority", 3))
        if rng.random() < 0.25:
            base_priority += rng.choice([-1, 1])
        priority = max(1, min(5, base_priority))

        synthetic_ops.append(
            Operation(
                operation_id=f"T{idx:0{width}d}",
                job_id=vehicle_id,
                duration=duration,
                resource_requirements=[
                    {"resource_type": "site", "possible_resource_ids": site_options},
                    {"resource_type": "vehicle", "possible_resource_ids": [vehicle_id]},
                ],
                precedence=[],
                metadata={
                    "test_type": test_type,
                    "priority": priority,
                    "source_template": template.operation_id,
                },
            )
        )

    return synthetic_ops


def sample_tests_with_safe_precedence(
    test_pool: Sequence[Operation],
    sample_size: int = 120,
    seed: Optional[int] = None,
    precedence_probability: float = 0.20,
    precedence_edge_ratio_cap: float = 0.12,
) -> List[Operation]:
    """
    Sample tests and add sparse precedence only among sampled tests.
    """
    if not test_pool:
        return []

    rng = random.Random(seed)
    sampled = list(rng.sample(list(test_pool), k=min(sample_size, len(test_pool))))

    # Recreate operations to keep sampled runs fully isolated.
    sampled_by_id: Dict[str, Operation] = {}
    for op in sampled:
        cloned = Operation(
            operation_id=op.operation_id,
            job_id=op.job_id,
            duration=float(op.duration),
            resource_requirements=[
                {
                    "resource_type": req.get("resource_type"),
                    "possible_resource_ids": list(req.get("possible_resource_ids", [])),
                }
                for req in op.get_resource_requirements()
            ],
            precedence=[],
            metadata=dict(op.metadata),
        )
        sampled_by_id[cloned.operation_id] = cloned

    sampled_ops = list(sampled_by_id.values())
    sampled_ops.sort(key=lambda op: int(op.operation_id[1:]))

    ops_by_vehicle: Dict[str, List[Operation]] = defaultdict(list)
    for op in sampled_ops:
        ops_by_vehicle[op.job_id].append(op)

    max_edges = int(len(sampled_ops) * precedence_edge_ratio_cap)
    edges_added = 0

    for vehicle_ops in ops_by_vehicle.values():
        if len(vehicle_ops) < 2:
            continue
        for idx in range(1, len(vehicle_ops)):
            if edges_added >= max_edges:
                break
            if rng.random() > precedence_probability:
                continue
            pred = vehicle_ops[idx - 1]
            succ = vehicle_ops[idx]
            succ.precedence = [pred.operation_id]
            edges_added += 1

    return sampled_ops


def generate_sampled_tests(
    base_tests: Sequence[Operation],
    pool_size: int = 500,
    sample_size: int = 120,
    seed: Optional[int] = None,
) -> List[Operation]:
    """
    Full pipeline: build random pool then sample subset with safe precedence.
    """
    pool = generate_random_test_pool(base_tests, pool_size=pool_size, seed=seed)
    # Use a derived seed so pool generation + sampling are independently stable.
    sample_seed = None if seed is None else seed + 1
    return sample_tests_with_safe_precedence(pool, sample_size=sample_size, seed=sample_seed)
