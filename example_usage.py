from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os

# Add the classes directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'classes'))

from classes.job import Job
from classes.operation import Operation
from classes.resource import Resource
from classes.schedule import Schedule

def create_example_schedule():
    """
    Example: Small manufacturing facility with 3 jobs that need to be processed
    - Job A: Make Widget A (needs machining then assembly)
    - Job B: Make Widget B (needs machining then painting then assembly)  
    - Job C: Make Widget C (needs machining then assembly)
    """
    
    # Create schedule for one week
    start_date = datetime(2024, 1, 1, 8, 0)  # Monday 8 AM
    end_date = datetime(2024, 1, 5, 17, 0)   # Friday 5 PM
    
    schedule = Schedule(
        name="Manufacturing Schedule - Week 1",
        schedule_id="SCHED_001",
        start_date=start_date,
        end_date=end_date
    )
    
    # Create resources (machines/workstations)
    resources = [
        Resource("MACHINE_001", "machining", "CNC Machine 1"),
        Resource("MACHINE_002", "machining", "CNC Machine 2"), 
        Resource("PAINT_001", "painting", "Paint Booth 1"),
        Resource("ASSEMBLY_001", "assembly", "Assembly Station 1"),
        Resource("ASSEMBLY_002", "assembly", "Assembly Station 2")
    ]
    
    # Add availability windows (8 AM to 5 PM, Monday to Friday)
    work_hours = []
    for day in range(5):  # 5 work days
        day_start = start_date + timedelta(days=day)
        day_end = day_start.replace(hour=17)  # 5 PM
        work_hours.append((day_start.timestamp(), day_end.timestamp()))
    
    for resource in resources:
        resource.availability_windows = work_hours
        schedule.add_resource(resource)
    
    # Create operations for Job A (Widget A)
    job_a_ops = [
        Operation(
            operation_id="A_MACH",
            job_id="JOB_A", 
            duration=timedelta(hours=2).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACHINE_001", "MACHINE_002"],
            precedence=[],  # No prerequisites
            metadata={"description": "Machine Widget A components"}
        ),
        Operation(
            operation_id="A_ASSY",
            job_id="JOB_A",
            duration=timedelta(hours=1).total_seconds(), 
            resource_type="assembly",
            possible_resource_ids=["ASSEMBLY_001", "ASSEMBLY_002"],
            precedence=["A_MACH"],  # Must complete machining first
            metadata={"description": "Assemble Widget A"}
        )
    ]
    
    # Create operations for Job B (Widget B)
    job_b_ops = [
        Operation(
            operation_id="B_MACH",
            job_id="JOB_B",
            duration=timedelta(hours=3).total_seconds(),
            resource_type="machining", 
            possible_resource_ids=["MACHINE_001", "MACHINE_002"],
            precedence=[],
            metadata={"description": "Machine Widget B components"}
        ),
        Operation(
            operation_id="B_PAINT",
            job_id="JOB_B",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="painting",
            possible_resource_ids=["PAINT_001"],
            precedence=["B_MACH"],
            metadata={"description": "Paint Widget B"}
        ),
        Operation(
            operation_id="B_ASSY", 
            job_id="JOB_B",
            duration=timedelta(hours=1).total_seconds(),
            resource_type="assembly",
            possible_resource_ids=["ASSEMBLY_001", "ASSEMBLY_002"],
            precedence=["B_PAINT"],  # Must complete painting first
            metadata={"description": "Assemble Widget B"}
        )
    ]
    
    # Create operations for Job C (Widget C)
    job_c_ops = [
        Operation(
            operation_id="C_MACH",
            job_id="JOB_C",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACHINE_001", "MACHINE_002"], 
            precedence=[],
            metadata={"description": "Machine Widget C components"}
        ),
        Operation(
            operation_id="C_ASSY",
            job_id="JOB_C", 
            duration=timedelta(hours=0.5).total_seconds(),
            resource_type="assembly",
            possible_resource_ids=["ASSEMBLY_001", "ASSEMBLY_002"],
            precedence=["C_MACH"],
            metadata={"description": "Assemble Widget C"}
        )
    ]
    
    # Create jobs
    jobs = [
        Job("JOB_A", job_a_ops, {"customer": "ABC Corp", "priority": "high"}),
        Job("JOB_B", job_b_ops, {"customer": "XYZ Inc", "priority": "medium"}), 
        Job("JOB_C", job_c_ops, {"customer": "123 Ltd", "priority": "low"})
    ]
    
    # Add jobs to schedule
    for job in jobs:
        schedule.add_job(job)
    
    return schedule

def schedule_operations(schedule: Schedule):
    """
    Simple scheduling algorithm - schedule operations as early as possible
    """
    print("=== Scheduling Operations ===")
    
    # Start scheduling from Monday 8 AM
    current_time = schedule.start_date
    
    # Try to schedule all operations
    scheduled_count = 0
    max_attempts = 100  # Prevent infinite loops
    
    while scheduled_count < len(schedule.operations) and max_attempts > 0:
        max_attempts -= 1
        initial_count = scheduled_count
        
        for op_id, operation in schedule.operations.items():
            if operation.is_scheduled():
                continue
                
            # Try to schedule this operation at the current time
            for resource_id in operation.possible_resource_ids:
                try:
                    if schedule.schedule_operation(op_id, resource_id, current_time):
                        scheduled_count += 1
                        print(f"✓ Scheduled {op_id} on {resource_id} at {current_time}")
                        break
                except (KeyError, ValueError) as e:
                    print(f"✗ Cannot schedule {op_id} on {resource_id}: {e}")
                    continue
        
        # If no progress, advance time by 30 minutes
        if scheduled_count == initial_count:
            current_time += timedelta(minutes=30)
            
        # Don't go past end of schedule
        if current_time > schedule.end_date:
            break
    
    print(f"\nScheduled {scheduled_count} out of {len(schedule.operations)} operations")
    return scheduled_count

def print_schedule_summary(schedule: Schedule):
    """
    Print a summary of the scheduled operations
    """
    print(f"\n=== Schedule Summary: {schedule.name} ===")
    print(f"Period: {schedule.start_date} to {schedule.end_date}")
    print(f"Jobs: {len(schedule.jobs)}")
    print(f"Resources: {len(schedule.resources)}")
    print(f"Operations: {len(schedule.operations)}")
    
    # Group operations by job
    print("\n--- Operations by Job ---")
    for job_id, job in schedule.jobs.items():
        print(f"\n{job_id} ({job.metadata.get('customer', 'Unknown')}):")
        job_ops = [op for op in job.operations if op.is_scheduled()]
        job_ops.sort()  # Sort by start time
        
        for op in job_ops:
            start_dt = datetime.fromtimestamp(op.start_time)
            end_dt = datetime.fromtimestamp(op.end_time)
            print(f"  {op.operation_id}: {start_dt.strftime('%a %H:%M')} - {end_dt.strftime('%a %H:%M')} on {op.resource_id}")
    
    # Show resource utilization
    print("\n--- Resource Utilization ---")
    for resource_id, resource in schedule.resources.items():
        print(f"\n{resource_id} ({resource.resource_name}):")
        if resource.schedule:
            for op in resource.schedule:
                start_dt = datetime.fromtimestamp(op.start_time)
                end_dt = datetime.fromtimestamp(op.end_time) 
                duration_hours = (op.end_time - op.start_time) / 3600
                print(f"  {start_dt.strftime('%a %H:%M')} - {end_dt.strftime('%a %H:%M')}: {op.operation_id} ({duration_hours:.1f}h)")
        else:
            print("  No operations scheduled")

def test_error_conditions(schedule: Schedule):
    """
    Test error handling and edge cases
    """
    print("\n=== Testing Error Conditions ===")
    
    # Try to schedule non-existent operation
    try:
        schedule.schedule_operation("FAKE_OP", "MACHINE_001", schedule.start_date)
        print("✗ Should have failed for non-existent operation")
    except KeyError as e:
        print(f"✓ Correctly caught error for non-existent operation: {e}")
    
    # Try to schedule on non-existent resource
    try:
        op_id = list(schedule.operations.keys())[0]
        schedule.schedule_operation(op_id, "FAKE_RESOURCE", schedule.start_date)
        print("✗ Should have failed for non-existent resource")
    except KeyError as e:
        print(f"✓ Correctly caught error for non-existent resource: {e}")
    
    # Try to schedule operation on incompatible resource type
    try:
        # Find a machining operation and try to schedule it on painting resource
        machining_op = None
        for op in schedule.operations.values():
            if op.resource_type == "machining" and not op.is_scheduled():
                machining_op = op
                break
        
        if machining_op:
            schedule.schedule_operation(machining_op.operation_id, "PAINT_001", schedule.start_date)
            print("✗ Should have failed for incompatible resource type")
    except ValueError as e:
        print(f"✓ Correctly caught error for incompatible resource type: {e}")

def main():
    """
    Main function to run the scheduling example
    """
    print("Manufacturing Scheduling Library Example")
    print("=" * 50)
    
    # Create the example schedule
    schedule = create_example_schedule()
    
    # Schedule the operations
    scheduled_count = schedule_operations(schedule)
    
    # Print summary
    print_schedule_summary(schedule)
    
    # Show interactive Gantt chart (will pop up in a window)
    print("\nDisplaying visual Gantt chart...")
    schedule.show_visual_gantt_chart()
    
    # Test error conditions
    test_error_conditions(schedule)
    
    print(f"\n=== Example Complete ===")
    print(f"Successfully demonstrated scheduling library with {scheduled_count} operations")

if __name__ == "__main__":
    main() 