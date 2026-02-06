"""
Example: 4 Resources, 5 Jobs Scenario

This example demonstrates the scheduling library with:
- 4 resources (2 machines, 1 welding station, 1 assembly station)
- 5 jobs with varying complexity (1-4 operations each)
- Different scheduling algorithms to compare results
- Use of the new utility functions for schedule analysis

This serves as a practical example of how to use the library for a
typical manufacturing scheduling problem.
"""

from datetime import datetime, timedelta
from typing import List
import sys
import os

# Add the classes directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'classes'))

from classes.job import Job
from classes.operation import Operation
from classes.resource import Resource
from classes.schedule import Schedule


def create_scenario():
    """
    Create a scheduling scenario with 4 resources and 5 jobs.
    
    Resources:
    - MACH_A, MACH_B: General machining resources
    - WELD_A: Welding station
    - ASSY_A: Assembly station
    
    Jobs:
    - JOB_1: Simple part (1 operation - machining only)
    - JOB_2: Two-step part (machining → assembly)
    - JOB_3: Simple weldment (welding → assembly)
    - JOB_4: Complex part (machining → welding → machining → assembly)
    - JOB_5: Standard part (machining → welding → assembly)
    
    Returns:
        Schedule: Configured schedule ready for operation scheduling
    """
    
    # Define the scheduling period (one work day: 8 AM to 5 PM)
    start_date = datetime(2024, 11, 4, 8, 0)  # Monday 8 AM
    end_date = datetime(2024, 11, 4, 17, 0)   # Monday 5 PM
    
    schedule = Schedule(
        name="Custom Manufacturing Schedule",
        schedule_id="CUSTOM_001",
        start_date=start_date,
        end_date=end_date
    )
    
    # === CREATE 4 RESOURCES ===
    resources = [
        Resource("MACH_A", "machining", "CNC Machine A"),
        Resource("MACH_B", "machining", "CNC Machine B"),
        Resource("WELD_A", "welding", "Welding Station A"),
        Resource("ASSY_A", "assembly", "Assembly Station A")
    ]
    
    # Set availability (8 AM to 5 PM)
    work_window = [(start_date.timestamp(), end_date.timestamp())]
    for resource in resources:
        resource.availability_windows = work_window
        schedule.add_resource(resource)
    
    print("=== Resources Created ===")
    for resource in resources:
        print(f"  {resource}")
    
    # === CREATE 5 JOBS WITH VARYING OPERATIONS ===
    
    # JOB 1: Simple part (1 operation)
    job1_ops = [
        Operation(
            operation_id="J1_MACH",
            job_id="JOB_1",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACH_A", "MACH_B"],
            precedence=[],
            metadata={"description": "Machine simple bracket"}
        )
    ]
    job1 = Job("JOB_1", job1_ops, {"customer": "Customer A", "priority": "medium", "part": "Bracket"})
    
    # JOB 2: Two-step part (2 operations)
    job2_ops = [
        Operation(
            operation_id="J2_MACH",
            job_id="JOB_2",
            duration=timedelta(hours=2).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACH_A", "MACH_B"],
            precedence=[],
            metadata={"description": "Machine housing components"}
        ),
        Operation(
            operation_id="J2_ASSY",
            job_id="JOB_2",
            duration=timedelta(hours=1).total_seconds(),
            resource_type="assembly",
            possible_resource_ids=["ASSY_A"],
            precedence=["J2_MACH"],
            metadata={"description": "Assemble housing"}
        )
    ]
    job2 = Job("JOB_2", job2_ops, {"customer": "Customer B", "priority": "high", "part": "Housing"})
    
    # JOB 3: Simple weldment (2 operations)
    job3_ops = [
        Operation(
            operation_id="J3_WELD",
            job_id="JOB_3",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="welding",
            possible_resource_ids=["WELD_A"],
            precedence=[],
            metadata={"description": "Weld frame components"}
        ),
        Operation(
            operation_id="J3_ASSY",
            job_id="JOB_3",
            duration=timedelta(hours=0.5).total_seconds(),
            resource_type="assembly",
            possible_resource_ids=["ASSY_A"],
            precedence=["J3_WELD"],
            metadata={"description": "Final assembly of frame"}
        )
    ]
    job3 = Job("JOB_3", job3_ops, {"customer": "Customer C", "priority": "low", "part": "Frame"})
    
    # JOB 4: Complex part (4 operations)
    job4_ops = [
        Operation(
            operation_id="J4_MACH1",
            job_id="JOB_4",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACH_A", "MACH_B"],
            precedence=[],
            metadata={"description": "Rough machining"}
        ),
        Operation(
            operation_id="J4_WELD",
            job_id="JOB_4",
            duration=timedelta(hours=1).total_seconds(),
            resource_type="welding",
            possible_resource_ids=["WELD_A"],
            precedence=["J4_MACH1"],
            metadata={"description": "Weld reinforcement"}
        ),
        Operation(
            operation_id="J4_MACH2",
            job_id="JOB_4",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACH_A", "MACH_B"],
            precedence=["J4_WELD"],
            metadata={"description": "Finish machining"}
        ),
        Operation(
            operation_id="J4_ASSY",
            job_id="JOB_4",
            duration=timedelta(hours=0.5).total_seconds(),
            resource_type="assembly",
            possible_resource_ids=["ASSY_A"],
            precedence=["J4_MACH2"],
            metadata={"description": "Final assembly"}
        )
    ]
    job4 = Job("JOB_4", job4_ops, {"customer": "Customer D", "priority": "high", "part": "Complex Assembly"})
    
    # JOB 5: Standard part (3 operations)
    job5_ops = [
        Operation(
            operation_id="J5_MACH",
            job_id="JOB_5",
            duration=timedelta(hours=2).total_seconds(),
            resource_type="machining",
            possible_resource_ids=["MACH_A", "MACH_B"],
            precedence=[],
            metadata={"description": "Machine base plate"}
        ),
        Operation(
            operation_id="J5_WELD",
            job_id="JOB_5",
            duration=timedelta(hours=1.5).total_seconds(),
            resource_type="welding",
            possible_resource_ids=["WELD_A"],
            precedence=["J5_MACH"],
            metadata={"description": "Weld mounting points"}
        ),
        Operation(
            operation_id="J5_ASSY",
            job_id="JOB_5",
            duration=timedelta(hours=1).total_seconds(),
            resource_type="assembly",
            possible_resource_ids=["ASSY_A"],
            precedence=["J5_WELD"],
            metadata={"description": "Install hardware"}
        )
    ]
    job5 = Job("JOB_5", job5_ops, {"customer": "Customer E", "priority": "medium", "part": "Base Plate"})
    
    # Add all jobs to schedule
    for job in [job1, job2, job3, job4, job5]:
        schedule.add_job(job)
    
    print("\n=== Jobs Created ===")
    for job_id, job in schedule.jobs.items():
        print(f"  {job} - {job.metadata['part']}")
    
    return schedule


def greedy_earliest_scheduler(schedule: Schedule) -> int:
    """
    Simple greedy scheduling: schedule operations as early as possible.
    
    Algorithm:
    1. Start at the beginning of the scheduling period
    2. For each unscheduled operation:
       - Try to schedule it on the first available compatible resource
       - If successful, move to next operation
    3. If no operations can be scheduled, advance time by 15 minutes
    4. Repeat until all scheduled or time runs out
    
    Args:
        schedule: The schedule with jobs and resources
        
    Returns:
        int: Number of operations successfully scheduled
    """
    print("\n=== Running Greedy Earliest Scheduler ===")
    
    current_time = schedule.start_date
    scheduled_count = 0
    max_iterations = 200
    
    while scheduled_count < len(schedule.operations) and max_iterations > 0:
        max_iterations -= 1
        progress_made = False
        
        # Try to schedule each unscheduled operation
        for op_id, operation in schedule.operations.items():
            if operation.is_scheduled():
                continue
            
            # Check if operation can start now (precedence satisfied)
            if not operation.can_start_at(current_time.timestamp(), schedule.operations):
                continue
            
            # Try each possible resource
            for resource_id in operation.possible_resource_ids:
                if schedule.schedule_operation(op_id, resource_id, current_time):
                    scheduled_count += 1
                    progress_made = True
                    print(f"  [+] Scheduled {op_id} on {resource_id} at {current_time.strftime('%H:%M')}")
                    break
        
        # If no progress, advance time
        if not progress_made:
            current_time += timedelta(minutes=15)
        
        # Don't go past end of schedule
        if current_time > schedule.end_date:
            break
    
    print(f"\nScheduled {scheduled_count} out of {len(schedule.operations)} operations")
    return scheduled_count


def priority_based_scheduler(schedule: Schedule) -> int:
    """
    Priority-based scheduling: schedule high-priority jobs first.
    
    Algorithm:
    1. Sort jobs by priority (high > medium > low)
    2. For each job in priority order:
       - Schedule all its operations as early as possible
       - Respect precedence constraints
    3. Use resource's get_next_available_time() to efficiently find slots
    
    Args:
        schedule: The schedule with jobs and resources
        
    Returns:
        int: Number of operations successfully scheduled
    """
    print("\n=== Running Priority-Based Scheduler ===")
    
    # Sort jobs by priority
    priority_order = {"high": 3, "medium": 2, "low": 1}
    sorted_jobs = sorted(
        schedule.jobs.values(),
        key=lambda j: priority_order.get(j.metadata.get("priority", "medium"), 2),
        reverse=True
    )
    
    scheduled_count = 0
    
    for job in sorted_jobs:
        print(f"\n  Scheduling {job.job_id} (priority: {job.metadata.get('priority', 'medium')})")
        
        # Build topological order for operations (respecting precedence)
        ops_to_schedule = sorted(job.operations, key=lambda op: len(op.precedence))
        
        for operation in ops_to_schedule:
            if operation.is_scheduled():
                continue
            
            # Find earliest time this operation can start
            earliest_start = schedule.start_date.timestamp()
            
            # Check precedence - must start after predecessors complete
            for pred_id in operation.precedence:
                pred_op = schedule.operations.get(pred_id)
                if pred_op and pred_op.is_scheduled():
                    earliest_start = max(earliest_start, pred_op.end_time)
            
            # Try to schedule on each possible resource
            best_time = None
            best_resource = None
            
            for resource_id in operation.possible_resource_ids:
                resource = schedule.resources[resource_id]
                next_time = resource.get_next_available_time(operation.duration, earliest_start)
                
                if next_time is not None:
                    if best_time is None or next_time < best_time:
                        best_time = next_time
                        best_resource = resource_id
            
            # Schedule at best available time
            if best_resource:
                start_dt = datetime.fromtimestamp(best_time)
                if schedule.schedule_operation(operation.operation_id, best_resource, start_dt):
                    scheduled_count += 1
                    print(f"    [+] {operation.operation_id} on {best_resource} at {start_dt.strftime('%H:%M')}")
    
    print(f"\nScheduled {scheduled_count} out of {len(schedule.operations)} operations")
    return scheduled_count


def analyze_schedule(schedule: Schedule):
    """
    Demonstrate all the utility functions for schedule analysis.
    
    Args:
        schedule: The schedule to analyze
    """
    print("\n" + "="*60)
    print("=== SCHEDULE ANALYSIS (Using New Utility Functions) ===")
    print("="*60)
    
    # 1. Overall statistics
    schedule.print_schedule_statistics()
    
    # 2. Job-level analysis
    print("\n=== Job Completion Analysis ===")
    for job_id, job in schedule.jobs.items():
        if job.is_complete():
            start = datetime.fromtimestamp(job.get_start_time())
            end = datetime.fromtimestamp(job.get_end_time())
            makespan = job.get_makespan() / 3600
            total_duration = job.get_total_duration() / 3600
            
            print(f"\n{job_id} ({job.metadata['part']}):")
            print(f"  Status: [COMPLETE]")
            print(f"  Start: {start.strftime('%H:%M')}")
            print(f"  End: {end.strftime('%H:%M')}")
            print(f"  Makespan: {makespan:.2f} hours (wall clock time)")
            print(f"  Total Processing: {total_duration:.2f} hours")
            print(f"  Efficiency: {(total_duration / makespan * 100):.1f}% (processing vs. wall time)")
        else:
            scheduled = job.get_scheduled_operations()
            unscheduled = job.get_unscheduled_operations()
            print(f"\n{job_id} ({job.metadata['part']}):")
            print(f"  Status: [INCOMPLETE]")
            print(f"  Scheduled: {len(scheduled)}/{len(job.operations)} operations")
            if unscheduled:
                print(f"  Unscheduled: {[op.operation_id for op in unscheduled]}")
    
    # 3. Resource-level analysis
    print("\n=== Resource Utilization Analysis ===")
    for resource_id, resource in schedule.resources.items():
        if len(resource.schedule) > 0:
            start = schedule.start_date.timestamp()
            end = schedule.end_date.timestamp()
            utilization = resource.get_utilization(start, end)
            total_hours = resource.get_total_scheduled_time() / 3600
            gaps = resource.get_schedule_gaps(start, end)
            
            print(f"\n{resource_id} ({resource.resource_name}):")
            print(f"  Operations Scheduled: {len(resource.schedule)}")
            print(f"  Total Work Hours: {total_hours:.2f}h")
            print(f"  Utilization: {utilization:.1%}")
            print(f"  Idle Periods: {len(gaps)}")
            
            if gaps:
                print(f"  Gaps:")
                for gap_start, gap_end in gaps[:3]:  # Show first 3 gaps
                    gap_duration = (gap_end - gap_start) / 3600
                    gap_start_dt = datetime.fromtimestamp(gap_start)
                    print(f"    - {gap_start_dt.strftime('%H:%M')} ({gap_duration:.2f}h)")
        else:
            print(f"\n{resource_id} ({resource.resource_name}):")
            print(f"  Status: IDLE (no operations scheduled)")
    
    # 4. Find operations that could be moved
    print("\n=== Schedule Flexibility Analysis ===")
    scheduled_ops = schedule.get_scheduled_operations()
    
    for op_id, op in list(scheduled_ops.items())[:3]:  # Analyze first 3 for brevity
        # Find alternative resources and times
        current_time = datetime.fromtimestamp(op.start_time)
        available = schedule.find_available_resources(op_id, current_time)
        
        print(f"\n{op_id}:")
        print(f"  Currently: {op.resource_id} at {current_time.strftime('%H:%M')}")
        print(f"  Could also use: {[r for r in available if r != op.resource_id]}")


def compare_schedules():
    """
    Compare different scheduling approaches on the same problem.
    """
    print("\n" + "="*60)
    print("=== COMPARING SCHEDULING ALGORITHMS ===")
    print("="*60)
    
    # Test greedy approach
    print("\n### APPROACH 1: Greedy Earliest ###")
    schedule1 = create_scenario()
    count1 = greedy_earliest_scheduler(schedule1)
    stats1 = schedule1.get_schedule_statistics()
    
    # Test priority approach
    print("\n### APPROACH 2: Priority-Based ###")
    schedule2 = create_scenario()
    count2 = priority_based_scheduler(schedule2)
    stats2 = schedule2.get_schedule_statistics()
    
    # Compare results
    print("\n" + "="*60)
    print("=== COMPARISON RESULTS ===")
    print("="*60)
    print(f"\n{'Metric':<30} {'Greedy':<15} {'Priority-Based':<15}")
    print("-" * 60)
    print(f"{'Operations Scheduled':<30} {count1:<15} {count2:<15}")
    print(f"{'Complete Jobs':<30} {stats1['complete_jobs']:<15} {stats2['complete_jobs']:<15}")
    print(f"{'Makespan (hours)':<30} {stats1['makespan_hours']:<15.2f} {stats2['makespan_hours']:<15.2f}")
    print(f"{'Avg Utilization':<30} {stats1['avg_resource_utilization']:<15.1%} {stats2['avg_resource_utilization']:<15.1%}")
    
    # Determine winner
    print("\n### Analysis ###")
    if stats1['makespan_hours'] < stats2['makespan_hours']:
        print("[+] Greedy approach finished faster")
    elif stats2['makespan_hours'] < stats1['makespan_hours']:
        print("[+] Priority-based approach finished faster")
    else:
        print("[=] Both approaches finished in the same time")
    
    if stats1['avg_resource_utilization'] > stats2['avg_resource_utilization']:
        print("[+] Greedy approach had better resource utilization")
    elif stats2['avg_resource_utilization'] > stats1['avg_resource_utilization']:
        print("[+] Priority-based approach had better resource utilization")
    else:
        print("[=] Both approaches had the same resource utilization")
    
    return schedule1, schedule2


def main():
    """
    Main function demonstrating the complete workflow.
    """
    print("="*60)
    print("SCHEDULING LIBRARY EXAMPLE: 4 Resources, 5 Jobs")
    print("="*60)
    
    # Part 1: Create and schedule
    schedule = create_scenario()
    scheduled_count = priority_based_scheduler(schedule)
    
    # Part 2: Analyze the results
    analyze_schedule(schedule)
    
    # Part 3: Visualize
    print("\n=== TEXT GANTT CHART ===")
    schedule.create_gantt_chart()
    
    # Part 4: Compare different approaches
    print("\n" + "="*60)
    input("Press Enter to compare scheduling algorithms...")
    schedule1, schedule2 = compare_schedules()
    
    # Part 5: Show visual Gantt chart
    print("\n=== VISUAL GANTT CHART ===")
    print("Opening visual Gantt chart for priority-based schedule...")
    schedule2.show_visual_gantt_chart()
    
    print("\n" + "="*60)
    print("=== EXAMPLE COMPLETE ===")
    print("="*60)
    print("\nKey takeaways:")
    print("  1. Created 4 resources and 5 jobs with 1-4 operations each")
    print("  2. Demonstrated two different scheduling algorithms")
    print("  3. Used utility functions to analyze schedule quality")
    print("  4. Compared approaches to find the best strategy")
    print("  5. Visualized results with Gantt charts")
    print("\nThe library provides the framework - YOU define the scheduling logic!")


if __name__ == "__main__":
    main()

