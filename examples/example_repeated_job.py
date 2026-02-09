"""
Example: find best job order and show Gantt chart.
"""

from datetime import datetime, timedelta
from itertools import permutations
import sys
import os

# Ensure repo root is on the path so "classes" imports work
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from classes.job_template import JobTemplate
from classes.operation_template import OperationTemplate
from classes.constraints import (
    BlockingConstraint,
    ChangeoverConstraint,
    DueDateConstraint,
    WipLimitConstraint,
)
from classes.resource import Resource
from classes.schedule import Schedule


def build_job_A_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="A_OP1",
            duration=timedelta(minutes=15).total_seconds(),
            resource_type="processing",
            possible_resource_ids=["R1"],
            precedence=[],
            metadata={"description": "A_OP1 (15 min) on Resource 1"},
        ),
        OperationTemplate(
            template_id="A_OP2",
            duration=timedelta(minutes=15).total_seconds(),
            resource_type="packaging",
            possible_resource_ids=["R2"],
            precedence=["A_OP1"],
            metadata={"description": "A_OP2 (15 min) on Resource 2"},
        ),
        OperationTemplate(
            template_id="A_OP3",
            duration=timedelta(minutes=5).total_seconds(),
            resource_type="packaging",
            possible_resource_ids=["R2"],
            precedence=["A_OP2"],
            metadata={"description": "A_OP3 (5 min) on Resource 2"},
        ),
    ]

    return JobTemplate(
        template_id="JOB_A",
        operations=operations,
        metadata={"job_type": "A"},
    )


def build_job_B_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="B_OP1",
            duration=timedelta(minutes=25).total_seconds(),
            resource_type="processing",
            possible_resource_ids=["R1"],
            precedence=[],
            metadata={"description": "B_OP1 (25 min) on Resource 1"},
        ),
        OperationTemplate(
            template_id="B_OP2",
            duration=timedelta(minutes=5).total_seconds(),
            resource_type="packaging",
            possible_resource_ids=["R2"],
            precedence=["B_OP1"],
            metadata={"description": "B_OP2 (5 min) on Resource 2"},
        ),
    ]

    return JobTemplate(
        template_id="JOB_B",
        operations=operations,
        metadata={"job_type": "B"},
    )


def build_job_C_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="C_OP1",
            duration=timedelta(minutes=12).total_seconds(),
            resource_type="processing",
            possible_resource_ids=["R1"],
            precedence=[],
            metadata={"description": "C_OP1 (12 min) on Resource 1"},
        ),
        OperationTemplate(
            template_id="C_OP2",
            duration=timedelta(minutes=8).total_seconds(),
            resource_type="packaging",
            possible_resource_ids=["R2"],
            precedence=["C_OP1"],
            metadata={"description": "C_OP2 (8 min) on Resource 2"},
        ),
        OperationTemplate(
            template_id="C_OP3",
            duration=timedelta(minutes=20).total_seconds(),
            resource_type="processing",
            possible_resource_ids=["R1"],
            precedence=["C_OP2"],
            metadata={"description": "C_OP3 (20 min) on Resource 1"},
        ),
        OperationTemplate(
            template_id="C_OP4",
            duration=timedelta(minutes=6).total_seconds(),
            resource_type="packaging",
            possible_resource_ids=["R2"],
            precedence=["C_OP3"],
            metadata={"description": "C_OP4 (6 min) on Resource 2"},
        ),
    ]

    return JobTemplate(
        template_id="JOB_C",
        operations=operations,
        metadata={"job_type": "C"},
    )


def build_schedule(start_date: datetime, end_date: datetime) -> Schedule:
    schedule = Schedule(
        name="2026-01-01 Schedule",
        schedule_id="SCHED_20260101",
        start_date=start_date,
        end_date=end_date,
    )

    resource_1 = Resource("R1", "processing", "Resource 1")
    resource_2 = Resource("R2", "packaging", "Resource 2")
    schedule.add_resource(resource_1)
    schedule.add_resource(resource_2)

    schedule.add_constraint(BlockingConstraint())
    schedule.add_constraint(ChangeoverConstraint(changeover_minutes=0))
    schedule.add_constraint(DueDateConstraint())
    schedule.add_constraint(WipLimitConstraint(max_wip=3))

    return schedule


def build_schedule_for_order(order: list) -> Schedule:
    start_date = datetime(2026, 1, 1, 8, 0)
    end_date = datetime(2026, 1, 1, 18, 0)

    schedule = build_schedule(start_date, end_date)

    job_A_template = build_job_A_template()
    job_B_template = build_job_B_template()
    job_C_template = build_job_C_template()

    instance_counter = 1
    for job_code in order:
        if job_code == "A":
            template = job_A_template
        elif job_code == "B":
            template = job_B_template
        else:
            template = job_C_template

        schedule.schedule_job_template(
            template,
            instance_id=str(instance_counter),
            start_time=start_date,
        )
        instance_counter += 1

    return schedule


def main():
    base_jobs = ["A", "A", "A", "B", "B", "B", "C", "C", "C"]
    unique_orders = sorted(set(permutations(base_jobs)))

    best_orders = []
    best_seconds = None
    for order in unique_orders:
        schedule = build_schedule_for_order(list(order))
        total_seconds = schedule.get_total_operational_time()
        if best_seconds is None or total_seconds < best_seconds:
            best_seconds = total_seconds
            best_orders = [order]
        elif total_seconds == best_seconds:
            best_orders.append(order)

    best_minutes = best_seconds / 60 if best_seconds is not None else 0
    print(f"Shortest total time: {best_minutes:.1f} minutes")
    print("Best orders:")
    for order in best_orders:
        print(f"  {''.join(order)}")

    best_schedule = build_schedule_for_order(list(best_orders[0]))
    best_schedule.create_gantt_chart()
    best_schedule.show_visual_gantt_chart()


if __name__ == "__main__":
    main()
