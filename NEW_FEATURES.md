# New Utility Functions - Summary

This document summarizes the new utility functions added to the scheduling library to make it easier to work with schedules, jobs, operations, and resources.

## Operation Class - New Methods

### `unschedule()`
Clear scheduling information from an operation without removing it from a resource.

```python
operation.unschedule()
assert operation.start_time is None
```

### `can_start_at(time, operations_dict)`
Check if an operation can start at a specific time based on precedence constraints.

```python
can_start = operation.can_start_at(start_time.timestamp(), schedule.operations)
if can_start:
    print("Precedence constraints satisfied")
```

### `get_duration_hours()`
Get the operation duration in hours instead of seconds.

```python
duration_hours = operation.get_duration_hours()  # Returns 1.5 instead of 5400
```

### `__repr__()`
Better string representation for debugging.

```python
print(operation)  # Operation(id=OP_001, job=JOB_001, type=machining, duration=2.0h, status=scheduled)
```

---

## Job Class - New Methods

### `is_complete()`
Check if all operations in the job are scheduled.

```python
if job.is_complete():
    print("Job is fully scheduled!")
```

### `get_scheduled_operations()`
Get list of operations that have been scheduled.

```python
scheduled = job.get_scheduled_operations()
print(f"{len(scheduled)} operations scheduled")
```

### `get_unscheduled_operations()`
Get list of operations that need scheduling.

```python
unscheduled = job.get_unscheduled_operations()
for op in unscheduled:
    print(f"Still need to schedule: {op.operation_id}")
```

### `get_start_time()` and `get_end_time()`
Get when the job starts (earliest operation) and ends (latest operation).

```python
start = job.get_start_time()
end = job.get_end_time()
if start and end:
    print(f"Job runs from {datetime.fromtimestamp(start)} to {datetime.fromtimestamp(end)}")
```

### `get_makespan()`
Get the total time from first operation start to last operation end (wall clock time).

```python
makespan = job.get_makespan()
print(f"Job takes {makespan / 3600:.1f} hours total")
```

### `get_total_duration()`
Get the sum of all operation durations (total processing time).

```python
total = job.get_total_duration()
print(f"Job requires {total / 3600:.1f} hours of processing")
```

### `get_operations_by_resource_type(resource_type)`
Filter operations by resource type.

```python
machining_ops = job.get_operations_by_resource_type("machining")
```

### `__repr__()`
Better string representation for debugging.

```python
print(job)  # Job(id=JOB_001, operations=3, status=complete)
```

---

## Resource Class - New Methods

### `get_operation_at(time)`
Find what operation is running at a specific time.

```python
op = resource.get_operation_at(datetime(2024, 1, 1, 10, 0).timestamp())
if op:
    print(f"Resource is running {op.operation_id}")
```

### `get_next_available_time(duration, after)`
Find the next time slot where an operation can fit.

```python
# Find when we can schedule a 2-hour operation
next_time = resource.get_next_available_time(7200, current_time.timestamp())
if next_time:
    print(f"Can schedule at {datetime.fromtimestamp(next_time)}")
```

### `get_utilization(start, end)`
Calculate resource utilization (% busy time) in a time range.

```python
util = resource.get_utilization(day_start.timestamp(), day_end.timestamp())
print(f"Resource is {util * 100:.1f}% utilized")
```

### `get_schedule_gaps(start, end)`
Find all idle periods in the schedule.

```python
gaps = resource.get_schedule_gaps()
for gap_start, gap_end in gaps:
    duration = (gap_end - gap_start) / 3600
    print(f"Gap: {duration:.1f} hours")
```

### `clear_schedule()`
Remove all operations from the resource's schedule.

```python
resource.clear_schedule()
assert len(resource.schedule) == 0
```

### `get_total_scheduled_time()`
Get the total duration of all scheduled operations.

```python
total = resource.get_total_scheduled_time()
print(f"Resource has {total / 3600:.1f} hours scheduled")
```

### `__repr__()`
Better string representation for debugging.

```python
print(resource)  # Resource(id=MACH_A, type=machining, name=CNC Machine A, scheduled_ops=5)
```

---

## Schedule Class - New Methods

### `get_scheduled_operations()`
Get dictionary of all scheduled operations.

```python
scheduled = schedule.get_scheduled_operations()
print(f"{len(scheduled)} operations scheduled")
```

### `get_unscheduled_operations()`
Get dictionary of all unscheduled operations.

```python
unscheduled = schedule.get_unscheduled_operations()
for op_id, op in unscheduled.items():
    print(f"Need to schedule: {op_id}")
```

### `get_job_completion_time(job_id)`
Get when a specific job finishes.

```python
completion = schedule.get_job_completion_time("JOB_001")
if completion:
    print(f"Job completes at {datetime.fromtimestamp(completion)}")
```

### `get_makespan()`
Get overall schedule makespan (first to last operation).

```python
makespan = schedule.get_makespan()
if makespan:
    print(f"Schedule takes {makespan / 3600:.1f} hours")
```

### `get_resources_by_type(resource_type)`
Get all resources of a specific type.

```python
machines = schedule.get_resources_by_type("machining")
print(f"Found {len(machines)} machining resources")
```

### `find_available_resources(operation_id, start_time)`
Find which resources can perform an operation at a specific time.

```python
available = schedule.find_available_resources("OP_001", datetime(2024, 1, 1, 8, 0))
print(f"Can use resources: {available}")
```

### `validate_schedule()`
Check for conflicts and constraint violations.

```python
issues = schedule.validate_schedule()
if issues:
    print("Schedule has issues:", issues)
else:
    print("Schedule is valid!")
```

### `clear_all_schedules()`
Unschedule everything and reset.

```python
schedule.clear_all_schedules()
assert len(schedule.get_scheduled_operations()) == 0
```

### `get_schedule_statistics()`
Get comprehensive statistics dictionary.

```python
stats = schedule.get_schedule_statistics()
print(f"Utilization: {stats['avg_resource_utilization']:.1%}")
print(f"Makespan: {stats['makespan_hours']:.2f} hours")
print(f"Complete jobs: {stats['complete_jobs']}/{stats['total_jobs']}")
```

### `print_schedule_statistics()`
Print formatted statistics to console.

```python
schedule.print_schedule_statistics()
# Prints:
# === Schedule Statistics ===
# Operations: 15 total, 12 scheduled, 3 unscheduled
# Jobs: 5 total, 4 complete, 1 incomplete
# ...
```

---

## New Example File

**`example_custom_scenario.py`** - Comprehensive example demonstrating:
- Creating 4 resources (2 machines, 1 welding station, 1 assembly station)
- Creating 5 jobs with 1-4 operations each
- Two different scheduling algorithms (greedy and priority-based)
- Using all the new utility functions for analysis
- Comparing scheduling approaches
- Visualizing results

Run it with:
```bash
python example_custom_scenario.py
```

---

## Key Benefits

1. **Easier Schedule Analysis** - Quickly check what's scheduled, what's not, and where things are
2. **Better Resource Management** - Find available time slots, check utilization, identify gaps
3. **Job Tracking** - Easily see if jobs are complete and when they finish
4. **Schedule Validation** - Automatically check for conflicts and constraint violations
5. **Performance Metrics** - Get utilization rates, makespan, and other KPIs
6. **Flexibility** - Find alternative resources and times for operations

These utilities make it much easier to build scheduling algorithms and analyze their results!

