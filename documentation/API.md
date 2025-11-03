# Scheduling Library - API Documentation

Complete reference for all classes, methods, and attributes in the scheduling library.

## Table of Contents

- [Job](#job)
- [Operation](#operation)
- [Resource](#resource)
- [Schedule](#schedule)
- [Scheduling Types](#scheduling-types)

---

## Job

Represents a unit of work that needs to be completed, composed of one or more operations.

### Constructor

```python
Job(job_id: str, operations: List[Operation], metadata: Optional[dict] = None)
```

**Parameters:**
- `job_id` (str): Unique identifier for the job
- `operations` (List[Operation]): List of operations that make up this job
- `metadata` (Optional[dict]): Optional dictionary for storing additional information
  - Common keys: `customer`, `priority`, `due_date`, `order_number`

**Example:**
```python
job = Job(
    job_id="JOB_001",
    operations=[op1, op2, op3],
    metadata={
        "customer": "ABC Corp",
        "priority": "high",
        "due_date": datetime(2024, 1, 10)
    }
)
```

### Attributes

- `job_id` (str): Unique identifier
- `operations` (List[Operation]): Operations belonging to this job
- `metadata` (dict): Additional job information

---

## Operation

Represents a single step in a job that must be performed on a specific resource type for a defined duration.

### Constructor

```python
Operation(
    operation_id: str,
    job_id: str,
    duration: float,
    resource_type: str,
    possible_resource_ids: Optional[List[str]] = None,
    precedence: Optional[List[str]] = None,
    metadata: Optional[dict] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    resource_id: Optional[str] = None
)
```

**Parameters:**
- `operation_id` (str): Unique identifier for the operation
- `job_id` (str): ID of the job this operation belongs to
- `duration` (float): Duration in seconds
- `resource_type` (str): Type of resource required (e.g., "machining", "assembly")
- `possible_resource_ids` (Optional[List[str]]): List of specific resources that can perform this operation
- `precedence` (Optional[List[str]]): List of operation IDs that must complete before this one
- `metadata` (Optional[dict]): Additional operation information
- `start_time` (Optional[float]): Scheduled start time as Unix timestamp (set during scheduling)
- `end_time` (Optional[float]): Scheduled end time as Unix timestamp (set during scheduling)
- `resource_id` (Optional[str]): ID of assigned resource (set during scheduling)

**Example:**
```python
operation = Operation(
    operation_id="OP_001",
    job_id="JOB_001",
    duration=timedelta(hours=2).total_seconds(),  # 2 hours
    resource_type="machining",
    possible_resource_ids=["MACHINE_001", "MACHINE_002"],
    precedence=["OP_000"],  # Must wait for OP_000
    metadata={"description": "Machine widget components"}
)
```

### Attributes

- `operation_id` (str): Unique identifier
- `job_id` (str): Parent job ID
- `duration` (float): Duration in seconds
- `resource_type` (str): Required resource type
- `possible_resource_ids` (List[str]): Compatible resources
- `precedence` (List[str]): Predecessor operation IDs
- `metadata` (dict): Additional information
- `start_time` (Optional[float]): Scheduled start (Unix timestamp)
- `end_time` (Optional[float]): Scheduled end (Unix timestamp)
- `resource_id` (Optional[str]): Assigned resource

### Methods

#### `is_scheduled() -> bool`

Check if the operation has been scheduled.

**Returns:** `True` if both start_time and end_time are set, `False` otherwise.

**Example:**
```python
if operation.is_scheduled():
    print(f"Scheduled from {operation.start_time} to {operation.end_time}")
else:
    print("Not yet scheduled")
```

---

## Resource

Represents a machine, workstation, or other entity that can perform operations.

### Constructor

```python
Resource(
    resource_id: str,
    resource_type: str,
    resource_name: str,
    availability_windows: Optional[List[Tuple[float, float]]] = None
)
```

**Parameters:**
- `resource_id` (str): Unique identifier for the resource
- `resource_type` (str): Type of resource (must match operation resource types)
- `resource_name` (str): Human-readable name
- `availability_windows` (Optional[List[Tuple[float, float]]]): List of (start, end) timestamp tuples when the resource is available

**Example:**
```python
# Create a machine available 8 AM to 5 PM
work_start = datetime(2024, 1, 1, 8, 0).timestamp()
work_end = datetime(2024, 1, 1, 17, 0).timestamp()

resource = Resource(
    resource_id="MACHINE_001",
    resource_type="machining",
    resource_name="CNC Machine 1",
    availability_windows=[(work_start, work_end)]
)
```

### Attributes

- `resource_id` (str): Unique identifier
- `resource_type` (str): Type of resource
- `resource_name` (str): Human-readable name
- `availability_windows` (List[Tuple[float, float]]): Available time windows
- `schedule` (SortedList): Operations scheduled on this resource (automatically sorted)

### Methods

#### `is_available(start: float, end: float) -> bool`

Check if the resource is available during a time range.

**Parameters:**
- `start` (float): Start timestamp
- `end` (float): End timestamp

**Returns:** `True` if available, `False` if there's a conflict or outside availability windows.

**Algorithm:** Uses binary search (O(log n)) for efficient conflict detection.

**Example:**
```python
start = datetime(2024, 1, 1, 8, 0).timestamp()
end = datetime(2024, 1, 1, 10, 0).timestamp()

if resource.is_available(start, end):
    print("Resource is available")
```

#### `add_operation(operation: Operation) -> bool`

Add an operation to the resource's schedule.

**Parameters:**
- `operation` (Operation): The operation to schedule

**Returns:** `True` if successfully added, `False` if time slot not available.

**Raises:**
- `ValueError`: If operation missing start/end time or resource type doesn't match

**Example:**
```python
operation.start_time = datetime(2024, 1, 1, 8, 0).timestamp()
operation.end_time = datetime(2024, 1, 1, 9, 0).timestamp()

if resource.add_operation(operation):
    print("Operation added to resource schedule")
```

#### `remove_operation(operation: Operation)`

Remove an operation from the resource's schedule.

**Parameters:**
- `operation` (Operation): The operation to remove

**Example:**
```python
resource.remove_operation(operation)
```

---

## Schedule

Central class for managing jobs, operations, and resources in a scheduling system.

### Constructor

```python
Schedule(
    name: str,
    schedule_id: str,
    start_date: datetime,
    end_date: datetime
)
```

**Parameters:**
- `name` (str): Human-readable name
- `schedule_id` (str): Unique identifier
- `start_date` (datetime): Start of scheduling period
- `end_date` (datetime): End of scheduling period

**Example:**
```python
schedule = Schedule(
    name="Production Schedule - Week 1",
    schedule_id="SCHED_001",
    start_date=datetime(2024, 1, 1, 8, 0),
    end_date=datetime(2024, 1, 5, 17, 0)
)
```

### Attributes

- `name` (str): Schedule name
- `schedule_id` (str): Unique identifier
- `start_date` (datetime): Period start
- `end_date` (datetime): Period end
- `jobs` (Dict[str, Job]): Jobs indexed by job_id
- `resources` (Dict[str, Resource]): Resources indexed by resource_id
- `operations` (Dict[str, Operation]): All operations indexed by operation_id

### Methods

#### `add_job(job: Job)`

Add a job to the schedule.

**Parameters:**
- `job` (Job): The job to add

**Side effects:** Also registers all of the job's operations in the schedule's operations dictionary.

**Example:**
```python
schedule.add_job(job)
```

#### `add_resource(resource: Resource)`

Add a resource to the schedule.

**Parameters:**
- `resource` (Resource): The resource to add

**Example:**
```python
schedule.add_resource(resource)
```

#### `schedule_operation(operation_id: str, resource_id: str, start_time: datetime) -> bool`

Schedule an operation on a specific resource at a specific time.

**Parameters:**
- `operation_id` (str): ID of operation to schedule
- `resource_id` (str): ID of resource to use
- `start_time` (datetime): When to start

**Returns:** `True` if successful, `False` if resource not available or precedence not met.

**Raises:**
- `KeyError`: If operation_id or resource_id doesn't exist
- `ValueError`: If resource type doesn't match or resource not in allowed list

**Validation performed:**
1. Operation and resource exist
2. Resource type matches operation requirements
3. Resource is in operation's allowed list
4. Resource is available during time window
5. All precedence constraints satisfied

**Example:**
```python
start = datetime(2024, 1, 1, 8, 0)
success = schedule.schedule_operation("OP_001", "MACHINE_001", start)

if success:
    print("Operation scheduled")
else:
    print("Could not schedule - resource busy or precedence not met")
```

#### `unschedule_operation(operation_id: str)`

Remove an operation from its scheduled resource.

**Parameters:**
- `operation_id` (str): ID of operation to unschedule

**Raises:**
- `KeyError`: If operation_id doesn't exist

**Example:**
```python
schedule.unschedule_operation("OP_001")
# Operation can now be rescheduled
```

#### `create_gantt_chart()`

Print a text-based Gantt chart to stdout.

**Output includes:**
- Time range
- Operations grouped by job
- Visual bars representing duration
- Resource assignments

**Example:**
```python
schedule.create_gantt_chart()
```

**Sample output:**
```
=== Gantt Chart ===
Schedule: Production Schedule - Week 1
Time Range: Mon 08:00 - Mon 13:30

JOB_A (ABC Corp - high priority):
  A_MACH: Mon 08:00 |████████| 10:00 [MACHINE_001] (2.0h)
  A_ASSY: Mon 10:00 |████| 11:00 [ASSEMBLY_001] (1.0h)
```

#### `show_visual_gantt_chart() -> Optional[Tuple]`

Display an interactive graphical Gantt chart using matplotlib.

**Returns:** `(fig, ax)` tuple if successful, `None` if matplotlib not available or no operations.

**Requires:** matplotlib library

**Features:**
- Color-coded operations by job
- Resources on y-axis
- Time on x-axis
- Interactive zoom and pan
- Legend with job details

**Example:**
```python
schedule.show_visual_gantt_chart()
# Opens matplotlib window with interactive chart
```

---

## Scheduling Types

The library supports different scheduling paradigms:

### Job Shop Scheduling

Each job has a specific sequence of operations. Each operation:
- Must be performed on a specific resource type
- Has precedence constraints defining order
- Operations from different jobs can be interleaved

**Example:** Manufacturing where Job A needs machining then assembly, Job B needs painting then assembly.

### Flow Shop Scheduling

All jobs go through the same sequence of resources in the same order. Only arrival times and durations vary per job.

**Implementation:** Set all jobs to have operations with the same resource type sequence and precedence chain.

### Open Shop Scheduling

Jobs have a set of operations, but no required order. Operations are resource-specific but can be performed in any sequence.

**Implementation:** Set operations with empty `precedence` lists.

---

## Time Handling

The library uses **Unix timestamps** (float, seconds since epoch) internally for efficient calculations. The API accepts `datetime` objects which are automatically converted.

**Converting between datetime and timestamp:**
```python
from datetime import datetime

# datetime to timestamp
timestamp = datetime(2024, 1, 1, 8, 0).timestamp()

# timestamp to datetime
dt = datetime.fromtimestamp(timestamp)
```

**Duration in seconds:**
```python
from datetime import timedelta

# 2 hours as seconds
duration = timedelta(hours=2).total_seconds()  # 7200.0
```

---

## Error Handling

The library performs extensive validation and raises specific exceptions:

### KeyError

Raised when referencing non-existent entities:
```python
schedule.schedule_operation("INVALID_OP", "MACHINE_001", start)
# KeyError: Operation INVALID_OP not found

schedule.schedule_operation("OP_001", "INVALID_RESOURCE", start)
# KeyError: Resource INVALID_RESOURCE not found
```

### ValueError

Raised for invalid configurations:
```python
# Wrong resource type
operation.resource_type = "machining"
resource.resource_type = "painting"
schedule.schedule_operation(op_id, resource_id, start)
# ValueError: Resource with type painting is not allowed for operation with type machining

# Resource not in allowed list
operation.possible_resource_ids = ["MACHINE_001"]
schedule.schedule_operation(op_id, "MACHINE_002", start)
# ValueError: Resource MACHINE_002 is not allowed for operation OP_001

# Operation missing scheduling info
resource.add_operation(operation)  # operation.start_time is None
# ValueError: Operation must have start_time and end_time before scheduling
```

### Boolean Return Values

Methods return `False` (not an exception) when scheduling is not possible due to availability or precedence:

```python
# Resource is busy
success = schedule.schedule_operation(op_id, resource_id, start)
if not success:
    print("Resource not available or precedence not satisfied")
```

---

## Performance Considerations

### Efficient Conflict Detection

Resources use `SortedList` (from `sortedcontainers`) to maintain operations in chronological order. Availability checking uses binary search:

- **Time complexity:** O(log n) where n = number of operations on the resource
- **Alternative (naive):** O(n) checking all operations

### Scalability

The library is designed for medium-scale problems (hundreds to thousands of operations). For very large problems:

- Consider breaking into smaller sub-problems
- Implement custom indexing for faster operation lookup
- Use more sophisticated scheduling algorithms

---

## Best Practices

### 1. Use Type Hints

The library uses type hints throughout. Enable type checking in your IDE for better error detection.

### 2. Validate Input Data

Ensure:
- All operation IDs are unique
- All resource IDs are unique
- Precedence references valid operation IDs
- Possible resource IDs reference valid resources
- Resource types match between operations and resources

### 3. Handle Scheduling Failures

Always check return values:
```python
if not schedule.schedule_operation(op_id, resource_id, start):
    # Handle failure - try different resource or time
    pass
```

### 4. Use Metadata Effectively

Store domain-specific information in metadata dictionaries:
```python
job.metadata = {
    "customer": "ABC Corp",
    "priority": "high",
    "due_date": datetime(2024, 1, 10),
    "order_number": "ORD-12345",
    "special_requirements": ["rush", "quality_check"]
}
```

### 5. Implement Scheduling Algorithms Carefully

The library provides the framework but not the algorithm. Consider:
- Job priorities
- Resource availability
- Precedence constraints
- Optimization objectives (minimize makespan, lateness, etc.)

---

## Examples

See `example_usage.py` for a complete working example demonstrating all major features.

---

## Version History

- **1.0**: Initial release with core scheduling functionality
  - Job, Operation, Resource, Schedule classes
  - Precedence constraints
  - Availability windows
  - Text and visual Gantt charts

