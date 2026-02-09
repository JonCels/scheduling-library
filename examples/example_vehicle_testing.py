"""
Example: vehicle emissions testing plant (constraints exploration).

Goal: expose where the library falls short for this scenario.
This is NOT intended to be a fully working optimization model.
"""

from datetime import datetime, timedelta
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
from classes.constraints import ChangeoverConstraint


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
    # NOTE: We can model site eligibility via possible_resource_ids per test.
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
    ]
    for site in sites:
        schedule.add_resource(site)
    for vehicle in vehicles:
        schedule.add_resource(vehicle)

    # Example tests for vehicles (each test is an operation)
    # Each operation can only be scheduled on a subset of sites.
    tests = [
        Operation(
            operation_id="V001_TEST_A",
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
            operation_id="V001_TEST_B",
            job_id="VEHICLE_001",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_001"]},
            ],
            precedence=["V001_TEST_A"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="V002_TEST_A",
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
            operation_id="V003_TEST_C",
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
            operation_id="V004_TEST_D",
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
            operation_id="V002_TEST_B",
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
            operation_id="V002_TEST_C",
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
            operation_id="V003_TEST_A",
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
            operation_id="V003_TEST_E",
            job_id="VEHICLE_003",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_003"]},
            ],
            precedence=["V003_TEST_C"],
            metadata={"test_type": "E", "priority": 1},
        ),
        Operation(
            operation_id="V004_TEST_A",
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
            operation_id="V005_TEST_E",
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
            operation_id="V006_TEST_E",
            job_id="VEHICLE_006",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_006"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 3},
        ),
    ]

    # Jobs are vehicles (each vehicle has one or more tests)
    schedule.add_job(Job("VEHICLE_001", [tests[0], tests[1], tests[4]], metadata={"vehicle": "V001"}))
    schedule.add_job(Job("VEHICLE_002", [tests[2], tests[5], tests[6]], metadata={"vehicle": "V002"}))
    schedule.add_job(Job("VEHICLE_003", [tests[3], tests[7], tests[8]], metadata={"vehicle": "V003"}))
    schedule.add_job(Job("VEHICLE_004", [tests[9]], metadata={"vehicle": "V004"}))
    schedule.add_job(Job("VEHICLE_005", [tests[10]], metadata={"vehicle": "V005"}))
    schedule.add_job(Job("VEHICLE_006", [tests[11]], metadata={"vehicle": "V006"}))

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

    # --- Where the library falls short for this scenario ---
    #
    # 1) "Complete as many tests as possible before day ends" is an optimization objective.
    #    The library doesn't provide an objective function or solver; only feasibility checks.
    #
    # 2) There's no built-in "daily horizon" enforcement (hard end time) during scheduling.
    #    schedule_operation only checks resource availability, not schedule.end_date.
    #
    # 3) There's no built-in prioritization or objective handling.
    #    We can store priority in metadata, but the scheduler doesn't optimize by it.
    #
    # 4) No built-in batching or queueing rules (e.g., test must start immediately
    #    once a vehicle arrives, or vehicles can't move between sites without transport time).
    #
    # 5) No travel/transfer times between tests if vehicles must move sites.
    #
    # 6) No concurrency limits for shared equipment inside a site (site-level capacity > 1).
    #
    # 7) No built-in due-date or release-date modeling per test unless we add constraints.
    #
    # 8) No built-in "maximize throughput" heuristic; schedule is manual or greedy.
    #
    # 9) No built-in vehicle-based changeover at a site (now possible via ChangeoverConstraint).

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
        ready.sort(key=lambda op: (op.metadata.get("priority", 5), op.duration))

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

    print("Scheduled operations:", len(schedule.get_scheduled_operations()))
    if unscheduled_tests:
        print("\nUnscheduled tests:")
        for op in unscheduled_tests:
            print(f"  {op.operation_id} (priority {op.metadata.get('priority', 5)})")

    schedule.create_gantt_chart()
    schedule.show_visual_gantt_chart()
    #
    # In practice, we'd need:
    # - A solver or heuristic to choose which tests to schedule within the day
    # - A "horizon constraint" (end of day)
    # - Optional priorities / weights
    # - Optional transfer time constraints between sites
    #
    # This example intentionally does not attempt full scheduling.

    print("Vehicle testing scenario constructed.")


if __name__ == "__main__":
    main()
