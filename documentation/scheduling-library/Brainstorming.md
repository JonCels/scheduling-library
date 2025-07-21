
## Language ##
- A **Job** is a unit of work that needs to be completed
	- Composed of one or more operations
	- Ex: produce 1000 units of product A
	- Ex: execute test WEXF2R
- An **Operation** is a single step in a job
	- Must be performed on a specific resource with a defined duration
	- Ex: setup time on site 73
	- Ex: cooling in cooling tower 2
- A **Resource** is a machine, line, station, site, or labour unit that performs operations
	- Ex: site 73
	- Ex: cooling tower 2
	- Ex: Grunwald
- A **Schedule** is the mapping of operations to resources over time
	- Contains all jobs (scheduled or not)
	- Contains all resources and their assigned operations

**Gay Lea Example**:
- Schedule 1000 Kgs of 500140
- Job: 1000 Kgs of 500140
- Resources involved:
	- Byproduct HTST, sour cream tank 1, Grunwald
- Operations involved:
	- Run on byproduct htst, ferment in sour cream tank, package in packaging line
	
Types of scheduling:
- Job type scheduling
- Flow shop scheduling
- Open shop scheduling



## Job Shop Scheduling ##
- Each job is a sequence of operations
	- A, then B, then C
- Each operation is performed on a specific resource
- Operations have sequence rules
- Resources are exclusive


## Flow Shop Scheduling ##
- Jobs all go through the same sequence of resources
- Job arrival time and duration per operation vary

## Open Shop Scheduling ##
- Job has a set of operations
- Operations are resource specific, but not ordered


# Classes #
## Operation ##
```
operation_id
job_id
resource_id
duration
start_time
precedence
```

# Job #
```
job_id
operations
priority
```

# Resource #
```
resource_id
availability_windows
```

# Schedule #
```
jobs
resources
operations
```