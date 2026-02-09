from datetime import datetime, timedelta
from itertools import permutations
from typing import List
import sys
import os

# Ensure repo root is on the path so "classes" imports work
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from classes.job_template import JobTemplate
from classes.operation_template import OperationTemplate
from classes.constraints import ChangeoverConstraint, BlockingConstraint, Constraint
from classes.resource import Resource
from classes.schedule import Schedule


def main():
    start_date = datetime(2026, 2, 2, 6, 0);
    end_date = datetime(2026, 2, 6, 18, 0);

    schedule = Schedule(
        name="FOK Schedule - 2026-02-02 - 2026-02-06",
        schedule_id="FOK_SCHED_260202_06",
        start_date=start_date,
        end_date=end_date
    )

def build_module_A_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="MAO1",
            duration=timedelta(hours=2.5).total_seconds(),
            resource_type="prep_station",
            possible_resource_ids=["prep_station_1"],
            precedence=[],
            metadata={"description": "Module A in prep station"},
        ),
        OperationTemplate(
            template_id="MAO2",
            duration=timedelta(hours=5).total_seconds(),
            resource_type="enerpack_drop_station",
            possible_resource_ids=["enerpack_drop_station_1"],
            precedence=["MAO1"],
            metadata={"description": "Module A in enerpack drop station"},
        ),
        OperationTemplate(
            template_id="MAO3",
            duration=timedelta(hours=1.25).total_seconds(),
            resource_type="add_on_drop_station",
            possible_resource_ids=["add_on_drop_station_1"],
            precedence=["MAO2"],
            metadata={"description": "Module A in add on drop station"},
        ),
        OperationTemplate(
            template_id="MAO4",
            duration=timedelta(hours=8).total_seconds(),
            resource_type="parking_bay",
            possible_resource_ids=["parking_bay_1", "parking_bay_2", "parking_bay_3", "parking_bay_4", "parking_bay_5", "parking_bay_6", "parking_bay_7", "parking_bay_8"],
            precedence=["MAO3"],
            metadata={"description": "Module A in parking bay"},
        ),
    ];

    return JobTemplate(
        template_id="module_A",
        operations=operations,
        metadata={"module_type": "A"},
    );

def build_module_B_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="MBO1",
            duration=timedelta(hours=2).total_seconds(),
            resource_type="prep_station",
            possible_resource_ids=["prep_station_1"],
            precedence=[],
            metadata={"description": "Module B in prep station"},
        ),
        OperationTemplate(
            template_id="MBO2",
            duration=timedelta(hours=2).total_seconds(),
            resource_type="enerpack_drop_station",
            possible_resource_ids=["enerpack_drop_station_1"],
            precedence=["MBO1"],
            metadata={"description": "Module B in enerpack drop station"},
        ),
        OperationTemplate(
            template_id="MBO3",
            duration=timedelta(hours=4).total_seconds(),
            resource_type="add_on_drop_station",
            possible_resource_ids=["add_on_drop_station_1"],
            precedence=["MBO2"],
            metadata={"description": "Module B in add on drop station"},
        ),
        OperationTemplate(
            template_id="MBO4",
            duration=timedelta(hours=8).total_seconds(),
            resource_type="parking_bay",
            possible_resource_ids=["parking_bay_1", "parking_bay_2", "parking_bay_3", "parking_bay_4", "parking_bay_5", "parking_bay_6", "parking_bay_7", "parking_bay_8"],
            precedence=["MBO3"],
            metadata={"description": "Module B in parking bay"},
        ),
    ];

    return JobTemplate(
        template_id="module_B",
        operations=operations,
        metadata={"module_type": "B"},
    );

def build_module_C_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="MCO1",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="prep_station",
            possible_resource_ids=["prep_station_1"],
            precedence=[],
            metadata={"description": "Module C in prep station"},
        ),
        OperationTemplate(
            template_id="MCO2",
            duration=timedelta(hours=6.5).total_seconds(),
            resource_type="enerpack_drop_station",
            possible_resource_ids=["enerpack_drop_station_1"],
            precedence=["MCO1"],
            metadata={"description": "Module C in enerpack drop station"},
        ),
        OperationTemplate(
            template_id="MCO3",
            duration=timedelta(hours=8).total_seconds(),
            resource_type="parking_bay",
            possible_resource_ids=["parking_bay_1", "parking_bay_2", "parking_bay_3", "parking_bay_4", "parking_bay_5", "parking_bay_6", "parking_bay_7", "parking_bay_8"],
            precedence=["MCO2"],
            metadata={"description": "Module C in parking bay"},
        ),
    ];

    return JobTemplate(
        template_id="module_C",
        operations=operations,
        metadata={"module_type": "C"},
    );

def build_module_D_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="MDO1",
            duration=timedelta(hours=0.5).total_seconds(),
            resource_type="prep_station",
            possible_resource_ids=["prep_station_1"],
            precedence=[],
            metadata={"description": "Module D in prep station"},
        ),
        OperationTemplate(
            template_id="MDO2",
            duration=timedelta(hours=3).total_seconds(),
            resource_type="enerpack_drop_station",
            possible_resource_ids=["enerpack_drop_station_1"],
            precedence=["MDO1"],
            metadata={"description": "Module D in enerpack drop station"},
        ),
        OperationTemplate(
            template_id="MDO3",
            duration=timedelta(hours=1).total_seconds(),
            resource_type="add_on_drop_station",
            possible_resource_ids=["add_on_drop_station_1"],
            precedence=["MDO2"],
            metadata={"description": "Module D in add on drop station"},
        ),
        OperationTemplate(
            template_id="MDO4",
            duration=timedelta(hours=8).total_seconds(),
            resource_type="parking_bay",
            possible_resource_ids=["parking_bay_1", "parking_bay_2", "parking_bay_3", "parking_bay_4", "parking_bay_5", "parking_bay_6", "parking_bay_7", "parking_bay_8"],
            precedence=["MDO3"],
            metadata={"description": "Module D in parking bay"},
        ),
    ];

    return JobTemplate(
        template_id="module_D",
        operations=operations,
        metadata={"module_type": "D"},
    );

def build_resources() -> List[Resource]:
    resources = [
        Resource("prep_station_1", "prep_station", "Prep Station"),
        Resource("enerpack_drop_station_1", "enerpack_drop_station", "Enerpack Drop Station"),
        Resource("add_on_drop_station_1", "add_on_drop_station", "Add-on Drop Station"),
        Resource("parking_bay_1", "parking_bay", "Parking Bay 1"),
        Resource("parking_bay_2", "parking_bay", "Parking Bay 2"),
        Resource("parking_bay_3", "parking_bay", "Parking Bay 3"),
        Resource("parking_bay_4", "parking_bay", "Parking Bay 4"),
        Resource("parking_bay_5", "parking_bay", "Parking Bay 5"),
        Resource("parking_bay_6", "parking_bay", "Parking Bay 6"),
        Resource("parking_bay_7", "parking_bay", "Parking Bay 7"),
        Resource("parking_bay_8", "parking_bay", "Parking Bay 8"),
    ];
    return resources;

def build_constraints() -> List[Constraint]:
    constraints = [
        BlockingConstraint(),
        ChangeoverConstraint(changeover_minutes=15),
    ];
    return constraints;

def build_schedule(start_date: datetime, end_date: datetime) -> Schedule:
    # Build schedule
    schedule = Schedule(
        name=f"FOK Schedule - {start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}",
        schedule_id=f"FOK_SCHED_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}",
        start_date=start_date,
        end_date=end_date
    );

    # Define resources and schedule constraints
    resources = build_resources();
    for resource in resources:
        schedule.add_resource(resource);
    
    constraints = build_constraints();
    for constraint in constraints:
        schedule.add_constraint(constraint);
    
    return schedule;

def build_schedule_for_sequence(sequence: List[str]) -> Schedule:
    start_date = datetime(2026, 2, 2, 6, 0);
    end_date = datetime(2026, 2, 6, 18, 0);
    schedule = build_schedule(start_date, end_date);

    # Define job templates 
    module_A_template = build_module_A_template();
    module_B_template = build_module_B_template();
    module_C_template = build_module_C_template();
    module_D_template = build_module_D_template();

    instance_counter = 1;
    for module_id in sequence:
        if module_id == "A":
            template = module_A_template;
        elif module_id == "B":
            template = module_B_template;
        elif module_id == "C":
            template = module_C_template;
        else:
            template = module_D_template;

        schedule.schedule_job_template(
            template,
            instance_id=f"M{module_id}{instance_counter}",
            start_time=start_date
        );
        instance_counter += 1;

    return schedule;

def main():
    # Orders to make in week
    module_orders = [
        "A", "A",
        "B", "B",
        "C", "C", "C",
        "D", "D", "D",
    ];

    # For each sequence, build a schedule and calculate the total operational time
    unique_sequences = sorted(set(permutations(module_orders)))
    best_sequences = []
    best_seconds = None
    for sequence in unique_sequences:
        schedule = build_schedule_for_sequence(sequence)
        total_seconds = schedule.get_total_operational_time()
        if best_seconds is None or total_seconds < best_seconds:
            best_seconds = total_seconds
            best_sequences = [sequence]
        elif total_seconds == best_seconds:
            best_sequences.append(sequence)
    
    best_minutes = best_seconds / 60 if best_seconds is not None else 0
    print(f"Shortest total time: {best_minutes:.1f} minutes")
    print("Best sequences:")
    for sequence in best_sequences:
        print(f"  {''.join(sequence)}")

    best_schedule = build_schedule_for_sequence(list(best_sequences[0]))
    best_schedule.create_gantt_chart()
    best_schedule.show_visual_gantt_chart()

if __name__ == "__main__":
    main()