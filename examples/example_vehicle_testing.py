"""
Example: vehicle emissions testing plant (constraints exploration).
"""

from datetime import datetime, timedelta, time
from collections import defaultdict
import sys
import os

# Ensure repo root is on the path so "classes" imports work
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from classes.operation import Operation
from classes.job import Job
from classes.resource import Resource
from classes.schedule import Schedule
from classes.constraints import ChangeoverConstraint, ShiftConstraint


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


def main():
    start_date = datetime(2026, 3, 3, 6, 0)
    end_date = datetime(2026, 3, 3, 18, 0)

    schedule = Schedule(
        name="Vehicle Emissions Testing - Day 1",
        schedule_id="VEH_TEST_DAY_1",
        start_date=start_date,
        end_date=end_date,
    )

    # Resources: sites/garages with different equipment
    sites = [
        Resource("Site_1", "site", "Site 1"),
        Resource("Site_2", "site", "Site 2"),
        Resource("Site_3", "site", "Site 3"),
        Resource("Site_4", "site", "Site 4"),
        Resource("Site_5", "site", "Site 5"),
    ]
    vehicles = [
        Resource("VEHICLE_001", "vehicle", "Vehicle 001"),
        Resource("VEHICLE_002", "vehicle", "Vehicle 002"),
        Resource("VEHICLE_003", "vehicle", "Vehicle 003"),
        Resource("VEHICLE_004", "vehicle", "Vehicle 004"),
        Resource("VEHICLE_005", "vehicle", "Vehicle 005"),
        Resource("VEHICLE_006", "vehicle", "Vehicle 006"),
        Resource("VEHICLE_007", "vehicle", "Vehicle 007"),
        Resource("VEHICLE_008", "vehicle", "Vehicle 008"),
        Resource("VEHICLE_009", "vehicle", "Vehicle 009"),
        Resource("VEHICLE_010", "vehicle", "Vehicle 010"),
        Resource("VEHICLE_011", "vehicle", "Vehicle 011"),
        Resource("VEHICLE_012", "vehicle", "Vehicle 012"),
        Resource("VEHICLE_013", "vehicle", "Vehicle 013"),
        Resource("VEHICLE_014", "vehicle", "Vehicle 014"),
        Resource("VEHICLE_015", "vehicle", "Vehicle 015"),
        Resource("VEHICLE_016", "vehicle", "Vehicle 016"),
        Resource("VEHICLE_017", "vehicle", "Vehicle 017"),
        Resource("VEHICLE_018", "vehicle", "Vehicle 018"),
        Resource("VEHICLE_019", "vehicle", "Vehicle 019"),
        Resource("VEHICLE_020", "vehicle", "Vehicle 020"),
        Resource("VEHICLE_021", "vehicle", "Vehicle 021"),
        Resource("VEHICLE_022", "vehicle", "Vehicle 022"),
        Resource("VEHICLE_023", "vehicle", "Vehicle 023"),
        Resource("VEHICLE_024", "vehicle", "Vehicle 024"),
    ]
    for site in sites:
        schedule.add_resource(site)
    for vehicle in vehicles:
        schedule.add_resource(vehicle)

    # Example tests for vehicles (each test is an operation)
    tests = [
        Operation(
            operation_id="T001",
            job_id="VEHICLE_001",
            duration=timedelta(hours=2).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_001"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T002",
            job_id="VEHICLE_001",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_001"]},
            ],
            precedence=["T001"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T003",
            job_id="VEHICLE_002",
            duration=timedelta(hours=2).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_002"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 3},
        ),
        Operation(
            operation_id="T004",
            job_id="VEHICLE_003",
            duration=timedelta(hours=3).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_003"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 1},
        ),
        Operation(
            operation_id="T005",
            job_id="VEHICLE_001",
            duration=timedelta(hours=1).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_001"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T006",
            job_id="VEHICLE_002",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_002"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T007",
            job_id="VEHICLE_002",
            duration=timedelta(hours=2.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_002"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 4},
        ),
        Operation(
            operation_id="T008",
            job_id="VEHICLE_003",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_003"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T009",
            job_id="VEHICLE_003",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_003"]},
            ],
            precedence=["T004"],
            metadata={"test_type": "E", "priority": 1},
        ),
        Operation(
            operation_id="T010",
            job_id="VEHICLE_004",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_004"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T011",
            job_id="VEHICLE_005",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_005"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 2},
        ),
        Operation(
            operation_id="T012",
            job_id="VEHICLE_006",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_006"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 3},
        ),
        Operation(
            operation_id="T013",
            job_id="VEHICLE_007",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_007"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T014",
            job_id="VEHICLE_008",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_008"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 1},
        ),
        Operation(
            operation_id="T015",
            job_id="VEHICLE_009",
            duration=timedelta(hours=2.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_009"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 3},
        ),
        Operation(
            operation_id="T016",
            job_id="VEHICLE_001",
            duration=timedelta(hours=0.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_001"]},
            ],
            precedence=["T002"],
            metadata={"test_type": "E", "priority": 2},
        ),
        Operation(
            operation_id="T017",
            job_id="VEHICLE_003",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_003"]},
            ],
            precedence=["T008"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T018",
            job_id="VEHICLE_010",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_010"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T019",
            job_id="VEHICLE_011",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_011"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 3},
        ),
        Operation(
            operation_id="T020",
            job_id="VEHICLE_012",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_012"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 1},
        ),
        Operation(
            operation_id="T021",
            job_id="VEHICLE_013",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_013"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 4},
        ),
        Operation(
            operation_id="T022",
            job_id="VEHICLE_014",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_014"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 2},
        ),
        Operation(
            operation_id="T023",
            job_id="VEHICLE_015",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_015"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T024",
            job_id="VEHICLE_016",
            duration=timedelta(hours=2.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_016"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 3},
        ),
        Operation(
            operation_id="T025",
            job_id="VEHICLE_017",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_017"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T026",
            job_id="VEHICLE_018",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_018"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 4},
        ),
        Operation(
            operation_id="T027",
            job_id="VEHICLE_019",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_019"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 2},
        ),
        Operation(
            operation_id="T028",
            job_id="VEHICLE_020",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_020"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T029",
            job_id="VEHICLE_021",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_021"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 3},
        ),
        Operation(
            operation_id="T030",
            job_id="VEHICLE_022",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_022"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 1},
        ),
        Operation(
            operation_id="T031",
            job_id="VEHICLE_023",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_023"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 4},
        ),
        Operation(
            operation_id="T032",
            job_id="VEHICLE_024",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_024"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 2},
        ),
    ]

    for op in tests:
        op.metadata["label"] = op.operation_id

    site_demand_map = compute_priority_ranks_site_demand_with_precedence(tests)

    # Jobs are vehicles (each vehicle has one or more tests)
    schedule.add_job(Job("VEHICLE_001", [tests[0], tests[1], tests[4], tests[15]], metadata={"vehicle": "V001"}))
    schedule.add_job(Job("VEHICLE_002", [tests[2], tests[5], tests[6]], metadata={"vehicle": "V002"}))
    schedule.add_job(Job("VEHICLE_003", [tests[3], tests[7], tests[8], tests[16]], metadata={"vehicle": "V003"}))
    schedule.add_job(Job("VEHICLE_004", [tests[9]], metadata={"vehicle": "V004"}))
    schedule.add_job(Job("VEHICLE_005", [tests[10]], metadata={"vehicle": "V005"}))
    schedule.add_job(Job("VEHICLE_006", [tests[11]], metadata={"vehicle": "V006"}))
    schedule.add_job(Job("VEHICLE_007", [tests[12]], metadata={"vehicle": "V007"}))
    schedule.add_job(Job("VEHICLE_008", [tests[13]], metadata={"vehicle": "V008"}))
    schedule.add_job(Job("VEHICLE_009", [tests[14]], metadata={"vehicle": "V009"}))
    schedule.add_job(Job("VEHICLE_010", [tests[17]], metadata={"vehicle": "V010"}))
    schedule.add_job(Job("VEHICLE_011", [tests[18]], metadata={"vehicle": "V011"}))
    schedule.add_job(Job("VEHICLE_012", [tests[19]], metadata={"vehicle": "V012"}))
    schedule.add_job(Job("VEHICLE_013", [tests[20]], metadata={"vehicle": "V013"}))
    schedule.add_job(Job("VEHICLE_014", [tests[21]], metadata={"vehicle": "V014"}))
    schedule.add_job(Job("VEHICLE_015", [tests[22]], metadata={"vehicle": "V015"}))
    schedule.add_job(Job("VEHICLE_016", [tests[23]], metadata={"vehicle": "V016"}))
    schedule.add_job(Job("VEHICLE_017", [tests[24]], metadata={"vehicle": "V017"}))
    schedule.add_job(Job("VEHICLE_018", [tests[25]], metadata={"vehicle": "V018"}))
    schedule.add_job(Job("VEHICLE_019", [tests[26]], metadata={"vehicle": "V019"}))
    schedule.add_job(Job("VEHICLE_020", [tests[27]], metadata={"vehicle": "V020"}))
    schedule.add_job(Job("VEHICLE_021", [tests[28]], metadata={"vehicle": "V021"}))
    schedule.add_job(Job("VEHICLE_022", [tests[29]], metadata={"vehicle": "V022"}))
    schedule.add_job(Job("VEHICLE_023", [tests[30]], metadata={"vehicle": "V023"}))
    schedule.add_job(Job("VEHICLE_024", [tests[31]], metadata={"vehicle": "V024"}))

    # Shift constraint: strict 6-hour shifts
    schedule.add_constraint(
        ShiftConstraint(
            shift_windows=[(time(6, 0), time(12, 0)), (time(12, 0), time(18, 0))],
            mode="strict",
            resource_type_filter=["site", "vehicle"],
        )
    )

    # Changeover at sites when switching vehicles (no changeover when same vehicle)
    schedule.add_constraint(
        ChangeoverConstraint(
            changeover_minutes=10,
            key_from="assigned_resource",
            key_field="vehicle",
            resource_type_filter=["site"],
        )
    )

    # Transfer time between sites for the same vehicle
    schedule.add_constraint(
        ChangeoverConstraint(
            changeover_minutes=20,
            key_from="assigned_resource",
            key_field="site",
            resource_type_filter=["vehicle"],
        )
    )

    # Greedy scheduler (priority first)
    unscheduled = [op for op in schedule.operations.values()]
    unscheduled_tests = []
    while True:
        ready = [
            op for op in unscheduled
            if all(schedule.operations[p].is_scheduled() for p in op.precedence)
        ]
        if not ready:
            break
        ready.sort(key=lambda op: op.metadata.get("priority_rank", 10**9))

        progress = False
        for op in ready:
            earliest = start_date.timestamp()
            if op.precedence:
                earliest = max(earliest, max(schedule.operations[p].end_time for p in op.precedence))
            if not op.can_start_at(earliest, schedule.operations):
                continue
            try:
                start_ts, assigned = schedule._find_earliest_slot_any_resource(op, earliest)
            except RuntimeError:
                unscheduled.remove(op)
                unscheduled_tests.append(op)
                continue
            if start_ts + op.duration > end_date.timestamp():
                continue
            if schedule.schedule_operation_multi(
                op.operation_id, assigned, datetime.fromtimestamp(start_ts)
            ):
                unscheduled.remove(op)
                progress = True
            else:
                unscheduled.remove(op)
                unscheduled_tests.append(op)
        if not progress:
            break

    for op in list(unscheduled):
        unscheduled_tests.append(op)
        unscheduled.remove(op)

    stats = schedule.get_schedule_statistics()
    total_demand_seconds = sum(op.duration for op in tests)
    scheduled_seconds = sum(op.duration for op in schedule.get_scheduled_operations().values())
    unscheduled_seconds = total_demand_seconds - scheduled_seconds
    schedule_quality_score = (
        (scheduled_seconds / total_demand_seconds) * 100 if total_demand_seconds > 0 else 0.0
    )

    print("Scheduled operations:", len(schedule.get_scheduled_operations()))
    print("\nSchedule quality metrics:")
    print(f"  Scheduled workload: {scheduled_seconds / 3600:.2f}h / {total_demand_seconds / 3600:.2f}h")
    print(f"  Unscheduled workload time: {unscheduled_seconds / 3600:.2f}h")
    print(f"  Workload coverage score: {schedule_quality_score:.1f}%")
    print(f"  Makespan: {stats['makespan_hours']:.2f}h")
    print(f"  Avg resource utilization: {stats['avg_resource_utilization']:.1%}")
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
