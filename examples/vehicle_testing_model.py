"""
Vehicle emissions testing scheduling problem model.
Defines schedule, resources, tests, jobs, and constraints.
"""

from datetime import datetime, timedelta, time
from collections import defaultdict
import sys
import os

# Ensure repo root is on the path so "classes" imports work
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from classes.operation import Operation
from classes.job import Job
from classes.resource import Resource
from classes.schedule import Schedule
from classes.constraints import ChangeoverConstraint, ShiftConstraint, SoakConstraint


def build_vehicle_testing_problem():
    """
    Build the vehicle emissions testing scheduling problem.
    Returns: schedule, tests, sites, vehicles, start_date, end_date
    """
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
            metadata={"test_type": "E", "priority": 2, "soak_hours": 4},
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
        Operation(
            operation_id="T033",
            job_id="VEHICLE_004",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_004"]},
            ],
            precedence=["T010"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T034",
            job_id="VEHICLE_005",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_005"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 3},
        ),
        Operation(
            operation_id="T035",
            job_id="VEHICLE_006",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_006"]},
            ],
            precedence=["T012"],
            metadata={"test_type": "D", "priority": 2},
        ),
        Operation(
            operation_id="T036",
            job_id="VEHICLE_007",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_007"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 1},
        ),
        Operation(
            operation_id="T037",
            job_id="VEHICLE_008",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_008"]},
            ],
            precedence=["T014"],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T038",
            job_id="VEHICLE_009",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_009"]},
            ],
            precedence=["T015"],
            metadata={"test_type": "B", "priority": 1, "soak_hours": 3},
        ),
        Operation(
            operation_id="T039",
            job_id="VEHICLE_010",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_010"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T040",
            job_id="VEHICLE_011",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_011"]},
            ],
            precedence=["T019"],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T041",
            job_id="VEHICLE_012",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_012"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 1},
        ),
        Operation(
            operation_id="T042",
            job_id="VEHICLE_013",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_013"]},
            ],
            precedence=["T021"],
            metadata={"test_type": "A", "priority": 2},
        ),
        Operation(
            operation_id="T043",
            job_id="VEHICLE_014",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_014"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 3},
        ),
        Operation(
            operation_id="T044",
            job_id="VEHICLE_015",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_015"]},
            ],
            precedence=["T023"],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T045",
            job_id="VEHICLE_016",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_016"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 4},
        ),
        Operation(
            operation_id="T046",
            job_id="VEHICLE_017",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_017"]},
            ],
            precedence=["T025"],
            metadata={"test_type": "E", "priority": 2},
        ),
        Operation(
            operation_id="T047",
            job_id="VEHICLE_018",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_018"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T048",
            job_id="VEHICLE_019",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_019"]},
            ],
            precedence=["T027"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T049",
            job_id="VEHICLE_020",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_020"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 3},
        ),
        Operation(
            operation_id="T050",
            job_id="VEHICLE_021",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_021"]},
            ],
            precedence=["T029"],
            metadata={"test_type": "D", "priority": 2},
        ),
        Operation(
            operation_id="T051",
            job_id="VEHICLE_022",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_022"]},
            ],
            precedence=["T030"],
            metadata={"test_type": "E", "priority": 1, "soak_hours": 2},
        ),
        Operation(
            operation_id="T052",
            job_id="VEHICLE_024",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_024"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 3},
        ),
    ]

    for op in tests:
        op.metadata["label"] = op.operation_id

    # Jobs are vehicles; group operations by job_id so test additions stay maintenance-free.
    tests_by_job_id = defaultdict(list)
    for op in tests:
        tests_by_job_id[op.job_id].append(op)
    for job_ops in tests_by_job_id.values():
        job_ops.sort(key=lambda op: int(op.operation_id.replace("T", "")))
    for vehicle in vehicles:
        job_id = vehicle.resource_id
        if not tests_by_job_id.get(job_id):
            continue
        schedule.add_job(
            Job(
                job_id,
                tests_by_job_id[job_id],
                metadata={"vehicle": job_id.replace("VEHICLE_", "V")},
            )
        )

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

    # Soak lag for specific tests only (via metadata, e.g. soak_hours).
    schedule.add_constraint(SoakConstraint())

    return schedule, tests, sites, vehicles, start_date, end_date
