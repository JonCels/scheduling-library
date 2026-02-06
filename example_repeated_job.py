"""
Example: schedule three instances of Job A from a template.

Job A sequence:
  - A_OP1: 10 min on Resource 1
  - Op2: 15 min on Resource 2
  - Op3:  5 min on Resource 2

This script shows how a no-wait ("blocking") rule can be enforced so a job
does not leave Resource 1 until Resource 2 is ready for the next step.
"""

from datetime import datetime, timedelta
from itertools import permutations
import sys
import os

# Add the classes directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), "classes"))

from classes.job_template import JobTemplate, OperationTemplate
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
        blocking=True,
    )

def build_job_B_template() -> JobTemplate:
    operations = [
        OperationTemplate(
            template_id="B_OP1",
            duration=timedelta(minutes=25).total_seconds(),
            resource_type="processing",
            possible_resource_ids=["R1"],
            precedence=[],
            metadata={"description": "B_OP1 (15 min) on Resource 1"},
        ),
        OperationTemplate(
            template_id="B_OP2",
            duration=timedelta(minutes=5).total_seconds(),
            resource_type="packaging",
            possible_resource_ids=["R2"],
            precedence=["B_OP1"],
            metadata={"description": "B_OP2 (15 min) on Resource 2"},
        ),
    ]

    return JobTemplate(
        template_id="JOB_B",
        operations=operations,
        metadata={"job_type": "B"},
        blocking=True,
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
        blocking=True,
    )

def build_schedule(start_date: datetime, end_date: datetime) -> Schedule:
    schedule = Schedule(
        name="2026-01-01 Schedule",
        schedule_id="SCHED_20260101",
        start_date=start_date,
        end_date=end_date,
        changeover_minutes=0,
    )

    # Define two resources with unique types
    resource_1 = Resource("R1", "processing", "Resource 1")
    resource_2 = Resource("R2", "packaging", "Resource 2")
    schedule.add_resource(resource_1)
    schedule.add_resource(resource_2)

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
        template = job_A_template if job_code == "A" else job_B_template if job_code == "B" else job_C_template
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

    # Print Gantt for the first best order
    best_schedule = build_schedule_for_order(list(best_orders[0]))
    best_schedule.create_gantt_chart()
    best_schedule.show_visual_gantt_chart()


if __name__ == "__main__":
    main()
