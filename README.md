# Scheduling Library

A flexible Python library for job shop scheduling problems. Schedule operations on resources with support for precedence constraints, resource availability windows, and visual Gantt charts.

## Overview

This library provides a framework for modeling and solving scheduling problems common in manufacturing, testing, and other resource-constrained environments. It supports:

- **Job Shop Scheduling**: Schedule jobs composed of multiple operations
- **Precedence Constraints**: Define operation dependencies (A must complete before B)
- **Resource Availability**: Restrict when resources can work (work hours, maintenance windows)
- **Resource Types**: Operations can only be scheduled on compatible resource types
- **Flexible Resource Assignment**: Operations can specify multiple possible resources
- **Visualization**: Generate text and graphical Gantt charts

## Installation

### Prerequisites

- Python 3.7+
- `sortedcontainers` package (required)
- `matplotlib` package (optional, for visual Gantt charts)

### Install Dependencies

```bash
pip install sortedcontainers
pip install matplotlib  # Optional, for visual Gantt charts
```

## Quick Start

```python
from datetime import datetime, timedelta
from classes.job import Job
from classes.operation import Operation
from classes.resource import Resource
from classes.schedule import Schedule

# Create a schedule
schedule = Schedule(
    name="Production Schedule",
    schedule_id="SCHED_001",
    start_date=datetime(2024, 1, 1, 8, 0),
    end_date=datetime(2024, 1, 5, 17, 0)
)

# Add a resource
machine = Resource(
    resource_id="MACHINE_001",
    resource_type="machining",
    resource_name="CNC Machine 1"
)
schedule.add_resource(machine)

# Create operations for a job
operations = [
    Operation(
        operation_id="OP_001",
        job_id="JOB_001",
        duration=3600.0,  # 1 hour in seconds
        resource_type="machining",
        possible_resource_ids=["MACHINE_001"],
        precedence=[],  # No prerequisites
        metadata={"description": "Machine part A"}
    )
]

# Create and add a job
job = Job("JOB_001", operations, {"customer": "ABC Corp", "priority": "high"})
schedule.add_job(job)

# Schedule the operation
start_time = datetime(2024, 1, 1, 8, 0)
success = schedule.schedule_operation("OP_001", "MACHINE_001", start_time)

if success:
    print("Operation scheduled successfully!")
    schedule.create_gantt_chart()  # Print text Gantt chart
```

## Core Concepts

### Job

A **Job** represents a unit of work to be completed. It consists of one or more operations.

```python
job = Job(
    job_id="JOB_001",
    operations=[op1, op2],
    metadata={"customer": "ABC Corp", "priority": "high", "due_date": datetime(...)}
)
```

### Operation

An **Operation** is a single step in a job that must be performed on a specific resource type for a defined duration.

```python
operation = Operation(
    operation_id="OP_001",
    job_id="JOB_001",
    duration=3600.0,  # Duration in seconds
    resource_type="machining",  # Type of resource required
    possible_resource_ids=["MACHINE_001", "MACHINE_002"],  # Compatible resources
    precedence=["OP_000"],  # Must wait for OP_000 to complete
    metadata={"description": "Machine widget components"}
)
```

**Key attributes:**
- `duration`: Time required in seconds
- `resource_type`: Type of resource needed (must match a resource's type)
- `possible_resource_ids`: List of specific resources that can perform this operation
- `precedence`: List of operation IDs that must complete before this one can start

### Resource

A **Resource** represents a machine, workstation, or other entity that can perform operations.

```python
resource = Resource(
    resource_id="MACHINE_001",
    resource_type="machining",  # Must match operation resource types
    resource_name="CNC Machine 1",
    availability_windows=[(start_timestamp, end_timestamp), ...]
)
```

**Key attributes:**
- `resource_type`: Type of work this resource can perform
- `availability_windows`: Optional list of (start, end) timestamp tuples defining when the resource is available
- `schedule`: Automatically maintained sorted list of scheduled operations

### Schedule

The **Schedule** is the central orchestrator that manages all jobs, operations, and resources.

```python
schedule = Schedule(
    name="Production Schedule - Week 1",
    schedule_id="SCHED_001",
    start_date=datetime(2024, 1, 1, 8, 0),
    end_date=datetime(2024, 1, 5, 17, 0)
)
```

**Main methods:**
- `add_job(job)`: Add a job to the schedule
- `add_resource(resource)`: Add a resource to the schedule
- `schedule_operation(operation_id, resource_id, start_time)`: Schedule an operation
- `unschedule_operation(operation_id)`: Remove an operation from its resource
- `create_gantt_chart()`: Print a text-based Gantt chart
- `show_visual_gantt_chart()`: Display an interactive matplotlib Gantt chart

## Scheduling Operations

The library provides the framework for scheduling but **does not include a scheduling algorithm**. You must implement your own logic to decide when and where to schedule operations. See `example_usage.py` for a simple greedy scheduler example.

When you call `schedule.schedule_operation()`, the library validates:
1. ✓ Operation and resource exist
2. ✓ Resource type matches operation requirements
3. ✓ Resource is in the operation's allowed list
4. ✓ Resource is available during the time window
5. ✓ All precedence constraints are satisfied

## Validation and Error Handling

The library performs extensive validation:

```python
# Raises KeyError if operation or resource doesn't exist
schedule.schedule_operation("INVALID_OP", "MACHINE_001", start_time)

# Raises ValueError if resource type doesn't match
operation.resource_type = "machining"
resource.resource_type = "painting"
schedule.schedule_operation(op_id, resource_id, start_time)  # ValueError

# Returns False if resource is busy or precedence not met
success = schedule.schedule_operation(op_id, resource_id, start_time)
if not success:
    print("Resource not available or precedence not satisfied")
```

## Visualization

### Text Gantt Chart

```python
schedule.create_gantt_chart()
```

Output:
```
=== Gantt Chart ===
Schedule: Production Schedule - Week 1
Time Range: Mon 08:00 - Mon 13:30

JOB_A (ABC Corp - high priority):
  A_MACH: Mon 08:00 |████████| 10:00 [MACHINE_001] (2.0h)
  A_ASSY: Mon 10:00 |████| 11:00 [ASSEMBLY_001] (1.0h)
```

### Visual Gantt Chart (requires matplotlib)

```python
schedule.show_visual_gantt_chart()
```

Displays an interactive matplotlib window with:
- Color-coded operations by job
- Resources on the y-axis
- Time on the x-axis
- Legend with job details

## Example: Manufacturing Schedule

See `example_usage.py` for a complete working example that demonstrates:
- Creating a schedule with 5 resources and 3 jobs
- Defining operations with precedence constraints
- Implementing a simple scheduling algorithm
- Visualizing the results

Run the example:
```bash
python example_usage.py
```

## Architecture

The library uses several design patterns for efficiency:

### Efficient Conflict Detection

Resources use a `SortedList` to maintain operations in chronological order. When checking if a resource is available, binary search (O(log n)) is used instead of checking all operations (O(n)).

### Unix Timestamps

Times are stored internally as Unix timestamps (float) for efficient calculations and comparisons. The library accepts `datetime` objects in the API and converts them automatically.

### Type Safety

The library uses Python type hints throughout for better IDE support and code documentation.

## Advanced Usage

### Custom Metadata

All classes support a `metadata` dictionary for storing custom information:

```python
job = Job("JOB_001", operations, {
    "customer": "ABC Corp",
    "priority": "high",
    "due_date": datetime(2024, 1, 10),
    "order_number": "ORD-12345",
    "special_instructions": "Expedite"
})
```

### Availability Windows

Restrict when resources can work:

```python
# 8 AM to 5 PM, Monday through Friday
work_hours = []
for day in range(5):
    day_start = start_date + timedelta(days=day)
    day_end = day_start.replace(hour=17)
    work_hours.append((day_start.timestamp(), day_end.timestamp()))

resource.availability_windows = work_hours
```

### Unscheduling and Rescheduling

Operations can be unscheduled and rescheduled:

```python
# Unschedule an operation
schedule.unschedule_operation("OP_001")

# Reschedule it at a different time or resource
schedule.schedule_operation("OP_001", "MACHINE_002", new_start_time)
```

## Limitations and Future Enhancements

**Current limitations:**
- No built-in scheduling algorithms (intentional - you implement your own)
- No support for setup times between operations
- No support for batch operations or job splitting
- No support for resource capacity > 1 (e.g., a resource pool)

**Potential future enhancements:**
- Built-in scheduling algorithms (greedy, genetic algorithm, constraint programming)
- Setup time matrix between operation types
- Resource pools with multiple capacity
- Job priority-based scheduling
- Optimization objectives (minimize makespan, lateness, etc.)

## Contributing

This is a framework library designed to be extended. Contributions welcome for:
- Additional scheduling algorithms
- More visualization options
- Performance optimizations
- Additional validation and error handling

## License

MIT License - feel free to use and modify as needed.

## Authors

Created as a flexible scheduling framework for manufacturing and resource planning applications.

## See Also

- **API Documentation**: See `documentation/API.md` for detailed class and method documentation
- **Example Code**: `example_usage.py` demonstrates all major features
- **Class Documentation**: All classes have comprehensive docstrings
