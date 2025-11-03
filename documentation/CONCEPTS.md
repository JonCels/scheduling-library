# Scheduling Library - Concepts and Terminology

This document explains the conceptual foundation and terminology used in the scheduling library.

## Core Language

### Job

A **Job** is a unit of work that needs to be completed.

- Composed of one or more **operations**
- Operations may have ordering constraints (precedence)
- Can have metadata (customer, priority, due date, etc.)

**Examples:**
- Produce 1000 units of product A
- Execute test WEXF2R
- Manufacture Widget B for customer XYZ

### Operation

An **Operation** is a single step in a job.

- Must be performed on a specific **resource type** with a defined **duration**
- Can only start after predecessor operations complete (precedence constraints)
- Can be performed on any resource of the matching type (if multiple are available)

**Examples:**
- Setup time on site 73 (30 minutes)
- Cooling in cooling tower 2 (2 hours)
- Machining on CNC machine (1.5 hours)
- Assembly on assembly station (45 minutes)

### Resource

A **Resource** is a machine, line, station, site, or labor unit that performs operations.

- Has a **type** (e.g., "machining", "assembly", "painting")
- Can have **availability windows** (work hours, maintenance schedules)
- Maintains a **schedule** of assigned operations
- Can only perform one operation at a time (exclusive use)

**Examples:**
- Site 73 (a testing site)
- Cooling tower 2 (a cooling resource)
- Grunwald (a packaging line)
- CNC Machine 1 (a machining resource)

### Schedule

A **Schedule** is the mapping of operations to resources over time.

- Contains all jobs (scheduled and unscheduled)
- Contains all resources and their assigned operations
- Manages the assignment of operations to resources
- Enforces constraints (precedence, availability, resource types)

## Real-World Example: Gay Lea Foods

**Scenario:** Schedule production of 1000 Kgs of product 500140

**Job:** 1000 Kgs of 500140

**Resources involved:**
- Byproduct HTST (heat treatment)
- Sour cream tank 1 (fermentation)
- Grunwald (packaging line)

**Operations involved:**
1. Run on byproduct HTST (2 hours)
2. Ferment in sour cream tank (8 hours) - must follow operation 1
3. Package on Grunwald line (1.5 hours) - must follow operation 2

**Precedence:** Operation 1 → Operation 2 → Operation 3

This forms a **precedence chain** where each operation must complete before the next can begin.

## Types of Scheduling Problems

The library can model different categories of scheduling problems:

### Job Shop Scheduling

**Characteristics:**
- Each job is a sequence of operations (A → B → C)
- Each operation is performed on a specific resource type
- Operations have strict sequence rules (precedence constraints)
- Resources are exclusive (one operation at a time)
- Different jobs can have different operation sequences

**Example:**
- Job A: Machining → Assembly
- Job B: Machining → Painting → Assembly
- Job C: Painting → Assembly

**Use cases:** Manufacturing, testing, multi-step processes

### Flow Shop Scheduling

**Characteristics:**
- All jobs go through the same sequence of resources
- Job arrival time and duration per operation may vary
- Same resource sequence for every job

**Example:**
- All jobs: Cutting → Drilling → Assembly → Inspection
- Only durations and start times differ between jobs

**Use cases:** Assembly lines, sequential processing

### Open Shop Scheduling

**Characteristics:**
- Job has a set of operations
- Operations are resource-specific but not ordered
- No precedence constraints (operations can be done in any order)
- Total flexibility in sequencing

**Example:**
- Job requires: 2 hours machining, 1 hour painting, 1 hour inspection
- Can be done in any order

**Use cases:** Flexible manufacturing, service operations

## Implementation in the Library

### Job Shop Scheduling
Set up operations with precedence constraints:
```python
operations = [
    Operation(..., precedence=[]),  # First operation
    Operation(..., precedence=["OP_001"]),  # Depends on OP_001
    Operation(..., precedence=["OP_002"])  # Depends on OP_002
]
```

### Flow Shop Scheduling
Give all jobs the same resource type sequence and precedence chain:
```python
# Job A
job_a_ops = [
    Operation(..., resource_type="cutting", precedence=[]),
    Operation(..., resource_type="drilling", precedence=["A_CUT"]),
    Operation(..., resource_type="assembly", precedence=["A_DRILL"])
]

# Job B (same sequence, different durations)
job_b_ops = [
    Operation(..., resource_type="cutting", precedence=[]),
    Operation(..., resource_type="drilling", precedence=["B_CUT"]),
    Operation(..., resource_type="assembly", precedence=["B_DRILL"])
]
```

### Open Shop Scheduling
Set all operations with empty precedence lists:
```python
operations = [
    Operation(..., precedence=[]),  # No constraints
    Operation(..., precedence=[]),  # No constraints
    Operation(..., precedence=[])   # No constraints
]
```

## Constraints and Validation

The library enforces several types of constraints:

### 1. Resource Type Constraints

Operations can only be scheduled on resources of the matching type.

```python
operation.resource_type = "machining"
resource.resource_type = "machining"  # ✓ Match
resource.resource_type = "painting"   # ✗ Mismatch - ValueError
```

### 2. Resource Availability Constraints

Resources can have availability windows (work hours, shifts, etc.).

```python
resource.availability_windows = [
    (monday_8am_timestamp, monday_5pm_timestamp),
    (tuesday_8am_timestamp, tuesday_5pm_timestamp)
]
# Operations can only be scheduled within these windows
```

### 3. Resource Exclusivity Constraints

A resource can only perform one operation at a time.

```python
# If OP_001 is scheduled 8:00-10:00 on MACHINE_001
# Then OP_002 cannot be scheduled 9:00-11:00 on MACHINE_001 (overlap)
# But OP_002 can be scheduled 10:00-12:00 on MACHINE_001 (after)
```

### 4. Precedence Constraints

Operations must wait for their predecessors to complete.

```python
op2.precedence = ["OP_001"]
# OP_002 cannot start until OP_001 is complete
# OP_002.start_time must be >= OP_001.end_time
```

### 5. Resource Eligibility Constraints

Operations specify which specific resources can perform them.

```python
operation.possible_resource_ids = ["MACHINE_001", "MACHINE_002"]
# This operation can ONLY be scheduled on these two machines
# Not on MACHINE_003, even if it has the right type
```

## Scheduling Strategies

The library provides the framework but **not** the scheduling algorithm. You implement the logic for deciding when and where to schedule operations.

### Greedy / Earliest Start Time
Schedule operations as soon as possible on the first available resource.

**Pros:** Simple, fast
**Cons:** May not be optimal, can lead to resource imbalances

### Priority-Based
Schedule high-priority jobs first.

**Pros:** Meets important deadlines
**Cons:** Low-priority jobs may be delayed significantly

### Resource Balancing
Try to distribute work evenly across resources.

**Pros:** Better resource utilization
**Cons:** More complex, may increase makespan

### Constraint Programming
Use a CP solver to find optimal or near-optimal schedules.

**Pros:** Can find optimal solutions
**Cons:** Computationally expensive for large problems

### Genetic Algorithms / Metaheuristics
Use evolutionary or local search methods.

**Pros:** Can handle complex objectives, finds good solutions
**Cons:** No guarantee of optimality, requires tuning

## Performance Characteristics

### Time Complexity

**Checking resource availability:**
- O(log n) per check, where n = operations on that resource
- Uses binary search on sorted operation list

**Scheduling an operation:**
- O(log n) to check availability
- O(log n) to insert into resource schedule
- O(p) to check precedence, where p = number of predecessors

**Overall scheduling algorithm:**
- Depends on your implementation
- Greedy: O(m × r × log n) where m = operations, r = resources, n = operations per resource

### Space Complexity

- O(j + o + r) where j = jobs, o = operations, r = resources
- Additional O(o) for sorted lists in resources

## Common Patterns

### Pattern 1: Sequential Operations
Each operation in a job must follow the previous one:
```python
operations = [
    Operation(..., precedence=[]),
    Operation(..., precedence=[operations[0].operation_id]),
    Operation(..., precedence=[operations[1].operation_id])
]
```

### Pattern 2: Parallel Operations
Multiple operations can start simultaneously:
```python
operations = [
    Operation("OP_A", ..., precedence=[]),  # Can start immediately
    Operation("OP_B", ..., precedence=[]),  # Can also start immediately
    Operation("OP_C", ..., precedence=["OP_A", "OP_B"])  # Waits for both
]
```

### Pattern 3: Work Shifts
Resources available only during specific hours:
```python
# 8 AM to 5 PM, Monday through Friday
for day in range(5):
    start = work_week_start + timedelta(days=day, hours=8)
    end = work_week_start + timedelta(days=day, hours=17)
    availability.append((start.timestamp(), end.timestamp()))
```

### Pattern 4: Resource Pools
Multiple interchangeable resources of the same type:
```python
resources = [
    Resource("MACHINE_001", "machining", "CNC Machine 1"),
    Resource("MACHINE_002", "machining", "CNC Machine 2"),
    Resource("MACHINE_003", "machining", "CNC Machine 3")
]

operation.possible_resource_ids = ["MACHINE_001", "MACHINE_002", "MACHINE_003"]
# Scheduler can choose any available machine
```

## Design Philosophy

The library is designed with these principles:

1. **Separation of Concerns**: Framework (validation, data structures) is separate from algorithm (scheduling logic)
2. **Flexibility**: Support multiple scheduling paradigms and custom metadata
3. **Type Safety**: Use Python type hints for better IDE support and error detection
4. **Performance**: Efficient data structures (SortedList, binary search) for scalability
5. **Validation**: Comprehensive error checking to catch configuration mistakes early
6. **Visualization**: Built-in Gantt charts for schedule inspection and verification

## Glossary

- **Duration**: Length of time an operation takes (in seconds)
- **Makespan**: Total time from first operation start to last operation end
- **Precedence**: Ordering constraint between operations
- **Resource Type**: Category of resource (e.g., "machining", "assembly")
- **Timestamp**: Unix timestamp (seconds since epoch) used internally
- **Availability Window**: Time range when a resource can work
- **Metadata**: Custom key-value data attached to jobs/operations
- **Gantt Chart**: Visual representation of schedule showing operations over time

## Further Reading

- **API Documentation**: See `API.md` for detailed class and method reference
- **Example Code**: `example_usage.py` demonstrates complete workflow
- **README**: `README.md` for quick start and overview

