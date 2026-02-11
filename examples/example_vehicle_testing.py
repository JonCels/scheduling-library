"""
Example: vehicle emissions testing plant (constraints exploration).
"""

from datetime import datetime, timedelta, time
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
        Operation(
            operation_id="V007_TEST_A",
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
            operation_id="V008_TEST_B",
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
            operation_id="V009_TEST_C",
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
            operation_id="V001_TEST_E",
            job_id="VEHICLE_001",
            duration=timedelta(hours=0.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_001"]},
            ],
            precedence=["V001_TEST_B"],
            metadata={"test_type": "E", "priority": 2},
        ),
        Operation(
            operation_id="V003_TEST_B",
            job_id="VEHICLE_003",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_003"]},
            ],
            precedence=["V003_TEST_A"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="V010_TEST_A",
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
            operation_id="V011_TEST_B",
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
            operation_id="V012_TEST_C",
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
            operation_id="V013_TEST_D",
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
            operation_id="V014_TEST_E",
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
            operation_id="V015_TEST_A",
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
            operation_id="V016_TEST_B",
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
            operation_id="V017_TEST_C",
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
            operation_id="V018_TEST_D",
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
            operation_id="V019_TEST_E",
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
            operation_id="V020_TEST_A",
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
            operation_id="V021_TEST_B",
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
            operation_id="V022_TEST_C",
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
            operation_id="V023_TEST_D",
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
            operation_id="V024_TEST_E",
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

    # Normalize operation IDs to simple numeric strings
    id_map = {op.operation_id: str(i + 1).zfill(3) for i, op in enumerate(tests)}
    for op in tests:
        op.operation_id = id_map[op.operation_id]
        op.precedence = [id_map[p] for p in op.precedence]

    for op in tests:
        job_number = op.job_id.replace("VEHICLE_", "")
        test_type = op.metadata.get("test_type", "T")
        op.metadata["label"] = f"{job_number}-{test_type}"

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
    schedule.show_visual_gantt_chart(resource_type_filter=["site"], title_suffix="Sites", block=False)
    schedule.show_visual_gantt_chart(resource_type_filter=["vehicle"], title_suffix="Vehicles", block=True)

    print("Vehicle testing scenario constructed.")


if __name__ == "__main__":
    main()
