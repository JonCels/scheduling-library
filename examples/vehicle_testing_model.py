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
from classes.duration_policy import CallableDurationAdjustmentPolicy
from classes.constraints import ChangeoverConstraint, ShiftConstraint, SoakConstraint
from constraint_config import SCHEDULE_CONFIG, CONSTRAINT_CONFIG, DURATION_ADJUSTMENT_CONFIG


def build_vehicle_testing_problem():
    """
    Build the vehicle emissions testing scheduling problem.
    Returns: schedule, tests, sites, vehicles, start_date, end_date
    """
    start_cfg = SCHEDULE_CONFIG["start_date"]
    end_cfg = SCHEDULE_CONFIG["end_date"]
    start_date = datetime(
        start_cfg["year"], start_cfg["month"], start_cfg["day"], start_cfg["hour"], start_cfg["minute"]
    )
    end_date = datetime(
        end_cfg["year"], end_cfg["month"], end_cfg["day"], end_cfg["hour"], end_cfg["minute"]
    )

    schedule = Schedule(
        name=SCHEDULE_CONFIG["name"],
        schedule_id=SCHEDULE_CONFIG["schedule_id"],
        start_date=start_date,
        end_date=end_date,
    )

    def _duration_adjustment_seconds(_schedule, _operation, assigned_resources):
        config = DURATION_ADJUSTMENT_CONFIG
        base_minutes = float(config.get("base_additional_minutes", 0.0))
        adjustment_minutes = base_minutes

        resource_rules = config.get("resource_based_rules", {})
        target_resource_type = resource_rules.get("resource_type")
        if target_resource_type and assigned_resources:
            assigned_resource_id = assigned_resources.get(target_resource_type)
            if isinstance(assigned_resource_id, list):
                assigned_resource_id = assigned_resource_id[0] if assigned_resource_id else None
            if assigned_resource_id:
                number_part = "".join(ch for ch in str(assigned_resource_id) if ch.isdigit())
                resource_number = int(number_part) if number_part else None
                if resource_number is not None:
                    for rule in resource_rules.get("rules", []):
                        min_number = rule.get("id_number_min")
                        max_number = rule.get("id_number_max")
                        if min_number is not None and resource_number < int(min_number):
                            continue
                        if max_number is not None and resource_number > int(max_number):
                            continue
                        adjustment_minutes += float(rule.get("additional_minutes", 0.0))

        return adjustment_minutes * 60.0

    schedule.set_duration_adjustment_policy(
        CallableDurationAdjustmentPolicy(_duration_adjustment_seconds)
    )

    # Resources: sites/garages with different equipment
    sites = [Resource(f"Site_{i}", "site", f"Site {i}") for i in range(1, 11)]
    vehicles = [Resource(f"VEHICLE_{i:03d}", "vehicle", f"Vehicle {i:03d}") for i in range(1, 51)]

    for site in sites:
        schedule.add_resource(site);

    for vehicle in vehicles:
        schedule.add_resource(vehicle);


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
            duration=timedelta(hours=1.5).total_seconds(),
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
            duration=timedelta(hours=1.0).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            duration=timedelta(hours=1.0).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            metadata={"test_type": "B", "priority": 3, "soak_hours": 4},
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
            duration=timedelta(hours=2.0).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            metadata={"test_type": "B", "priority": 2, "soak_hours": 2},
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
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_008"]},
            ],
            precedence=["T014"],
            metadata={"test_type": "A", "priority": 2, "soak_hours": 4},
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            duration=timedelta(hours=1.0).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            duration=timedelta(hours=1.0).total_seconds(),
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
            duration=timedelta(hours=3.0).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
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
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_024"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 3},
        ),
    ]

    # Explicit tests T053–T102 (static entries, same values as previous generation logic)
    tests.extend([
        Operation(
            operation_id="T053",
            job_id="VEHICLE_025",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4", "Site_7"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_025"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T054",
            job_id="VEHICLE_025",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_025"]},
            ],
            precedence=["T053"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T055",
            job_id="VEHICLE_025",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_6"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_025"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2, "soak_hours": 2},
        ),
        Operation(
            operation_id="T056",
            job_id="VEHICLE_025",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_025"]},
            ],
            precedence=["T055"],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T057",
            job_id="VEHICLE_026",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_026"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T058",
            job_id="VEHICLE_026",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_6"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_026"]},
            ],
            precedence=["T057"],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T059",
            job_id="VEHICLE_026",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_026"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T060",
            job_id="VEHICLE_026",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_026"]},
            ],
            precedence=["T059"],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T061",
            job_id="VEHICLE_027",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_6"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_027"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T062",
            job_id="VEHICLE_027",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_027"]},
            ],
            precedence=["T061"],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T063",
            job_id="VEHICLE_027",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_027"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T064",
            job_id="VEHICLE_028",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_028"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T065",
            job_id="VEHICLE_028",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_028"]},
            ],
            precedence=["T064"],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T066",
            job_id="VEHICLE_028",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_6", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_028"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T067",
            job_id="VEHICLE_029",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_029"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T068",
            job_id="VEHICLE_029",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_6", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_029"]},
            ],
            precedence=["T067"],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T069",
            job_id="VEHICLE_029",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_7", "Site_10", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_029"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2, "soak_hours": 2},
        ),
        Operation(
            operation_id="T070",
            job_id="VEHICLE_030",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_6", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_030"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T071",
            job_id="VEHICLE_030",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_7", "Site_10", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_030"]},
            ],
            precedence=["T070"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T072",
            job_id="VEHICLE_030",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_8", "Site_1"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_030"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T073",
            job_id="VEHICLE_031",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_7", "Site_10", "Site_3"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_031"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T074",
            job_id="VEHICLE_031",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_8", "Site_1"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_031"]},
            ],
            precedence=["T073"],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T075",
            job_id="VEHICLE_031",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_9", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_031"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T076",
            job_id="VEHICLE_032",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_8", "Site_1"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_032"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T077",
            job_id="VEHICLE_032",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_9", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_032"]},
            ],
            precedence=["T076"],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T078",
            job_id="VEHICLE_032",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_10", "Site_3", "Site_6"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_032"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T079",
            job_id="VEHICLE_033",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_9", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_033"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T080",
            job_id="VEHICLE_033",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_10", "Site_3", "Site_6"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_033"]},
            ],
            precedence=["T079"],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T081",
            job_id="VEHICLE_033",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_033"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1, "soak_hours": 2},
        ),
        Operation(
            operation_id="T082",
            job_id="VEHICLE_034",
            duration=timedelta(hours=1).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_10", "Site_3", "Site_6"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_034"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T083",
            job_id="VEHICLE_034",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_034"]},
            ],
            precedence=["T082"],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T084",
            job_id="VEHICLE_034",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_034"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T085",
            job_id="VEHICLE_035",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_4"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_035"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T086",
            job_id="VEHICLE_035",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_035"]},
            ],
            precedence=["T085"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T087",
            job_id="VEHICLE_035",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_6", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_035"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T088",
            job_id="VEHICLE_036",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_5"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_036"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T089",
            job_id="VEHICLE_036",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_6", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_036"]},
            ],
            precedence=["T088"],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T090",
            job_id="VEHICLE_036",
            duration=timedelta(hours=2.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_036"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T091",
            job_id="VEHICLE_037",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_3", "Site_6", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_037"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T092",
            job_id="VEHICLE_037",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_037"]},
            ],
            precedence=["T091"],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T093",
            job_id="VEHICLE_037",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_037"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4, "soak_hours": 2},
        ),
        Operation(
            operation_id="T094",
            job_id="VEHICLE_038",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_4", "Site_7"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_038"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T095",
            job_id="VEHICLE_038",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_038"]},
            ],
            precedence=["T094"],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T096",
            job_id="VEHICLE_038",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_6", "Site_9", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_038"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T097",
            job_id="VEHICLE_039",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_5", "Site_8"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_039"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T098",
            job_id="VEHICLE_039",
            duration=timedelta(hours=2.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_6", "Site_9", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_039"]},
            ],
            precedence=["T097"],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T099",
            job_id="VEHICLE_039",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_7", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_039"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T100",
            job_id="VEHICLE_040",
            duration=timedelta(hours=0.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_6", "Site_9", "Site_2"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_040"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 1},
        ),
        Operation(
            operation_id="T101",
            job_id="VEHICLE_040",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_7", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_040"]},
            ],
            precedence=["T100"],
            metadata={"test_type": "B", "priority": 2},
        ),
        Operation(
            operation_id="T102",
            job_id="VEHICLE_040",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_8", "Site_1"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_040"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 2},
        ),
        Operation(
            operation_id="T103",
            job_id="VEHICLE_041",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_4", "Site_6", "Site_8", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_041"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T104",
            job_id="VEHICLE_041",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_5", "Site_7", "Site_8", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_041"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T105",
            job_id="VEHICLE_042",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3", "Site_4", "Site_5", "Site_6", "Site_8", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_042"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 5},
        ),
        Operation(
            operation_id="T106",
            job_id="VEHICLE_042",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3", "Site_4", "Site_5", "Site_6", "Site_7", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_042"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 3},
        ),
        Operation(
            operation_id="T107",
            job_id="VEHICLE_043",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_4", "Site_5", "Site_7", "Site_8", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_043"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 4},
        ),
        Operation(
            operation_id="T108",
            job_id="VEHICLE_043",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_4", "Site_6", "Site_7", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_043"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 5},
        ),
        Operation(
            operation_id="T109",
            job_id="VEHICLE_044",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3", "Site_4", "Site_5", "Site_6", "Site_8", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_044"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 3},
        ),
        Operation(
            operation_id="T110",
            job_id="VEHICLE_044",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3", "Site_4", "Site_5", "Site_7", "Site_8", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_044"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 4},
        ),
        Operation(
            operation_id="T111",
            job_id="VEHICLE_045",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_5", "Site_6", "Site_8", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_045"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 5},
        ),
        Operation(
            operation_id="T112",
            job_id="VEHICLE_045",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3", "Site_4", "Site_6", "Site_7", "Site_8", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_045"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 3},
        ),
        Operation(
            operation_id="T113",
            job_id="VEHICLE_046",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_4", "Site_5", "Site_6", "Site_7", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_046"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 4},
        ),
        Operation(
            operation_id="T114",
            job_id="VEHICLE_046",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3", "Site_4", "Site_5", "Site_6", "Site_8", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_046"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 5},
        ),
        Operation(
            operation_id="T115",
            job_id="VEHICLE_047",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3", "Site_4", "Site_5", "Site_7", "Site_8", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_047"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 3},
        ),
        Operation(
            operation_id="T116",
            job_id="VEHICLE_047",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_4", "Site_6", "Site_7", "Site_8", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_047"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 4},
        ),
        Operation(
            operation_id="T117",
            job_id="VEHICLE_048",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_4", "Site_5", "Site_6", "Site_8", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_048"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 5},
        ),
        Operation(
            operation_id="T118",
            job_id="VEHICLE_048",
            duration=timedelta(hours=2.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3", "Site_4", "Site_5", "Site_6", "Site_7", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_048"]},
            ],
            precedence=[],
            metadata={"test_type": "D", "priority": 3},
        ),
        Operation(
            operation_id="T119",
            job_id="VEHICLE_049",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_3", "Site_4", "Site_5", "Site_6", "Site_8", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_049"]},
            ],
            precedence=[],
            metadata={"test_type": "E", "priority": 4},
        ),
        Operation(
            operation_id="T120",
            job_id="VEHICLE_049",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_4", "Site_6", "Site_7", "Site_8", "Site_9"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_049"]},
            ],
            precedence=[],
            metadata={"test_type": "A", "priority": 5},
        ),
        Operation(
            operation_id="T121",
            job_id="VEHICLE_050",
            duration=timedelta(hours=1.0).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_2", "Site_3", "Site_4", "Site_5", "Site_7", "Site_8", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_050"]},
            ],
            precedence=[],
            metadata={"test_type": "B", "priority": 3},
        ),
        Operation(
            operation_id="T122",
            job_id="VEHICLE_050",
            duration=timedelta(hours=1.75).total_seconds(),
            resource_requirements=[
                {"resource_type": "site", "possible_resource_ids": ["Site_1", "Site_2", "Site_3", "Site_4", "Site_6", "Site_7", "Site_9", "Site_10"]},
                {"resource_type": "vehicle", "possible_resource_ids": ["VEHICLE_050"]},
            ],
            precedence=[],
            metadata={"test_type": "C", "priority": 4},
        ),
    ])

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

    shift_windows = {
        shift_name: (time(start_h, start_m), time(end_h, end_m))
        for shift_name, ((start_h, start_m), (end_h, end_m)) in CONSTRAINT_CONFIG["shift_windows"].items()
    }
    schedule.add_constraint(
        ShiftConstraint(
            shift_windows=list(shift_windows.values()),
            mode=CONSTRAINT_CONFIG["shift_mode"],
            resource_type_filter=CONSTRAINT_CONFIG["shift_resource_type_filter"],
        )
    )

    # Changeover at sites when switching vehicles (no changeover when same vehicle)
    schedule.add_constraint(
        ChangeoverConstraint(
            changeover_minutes=CONSTRAINT_CONFIG["site_changeover_minutes"],
            key_from="assigned_resource",
            key_field="vehicle",
            resource_type_filter=["site"],
        )
    )

    # Transfer time between sites for the same vehicle
    schedule.add_constraint(
        ChangeoverConstraint(
            changeover_minutes=CONSTRAINT_CONFIG["vehicle_transfer_minutes"],
            key_from="assigned_resource",
            key_field="site",
            resource_type_filter=["vehicle"],
        )
    )

    # Soak lag for specific tests only (via metadata, e.g. soak_hours).
    if CONSTRAINT_CONFIG["enable_soak_constraint"]:
        schedule.add_constraint(SoakConstraint())

    return schedule, tests, sites, vehicles, start_date, end_date
