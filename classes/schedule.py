"""
Schedule class for the scheduling library.

The Schedule is the central orchestrator that manages jobs, operations, and resources,
and provides methods for scheduling operations and visualizing the results.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, List, TYPE_CHECKING
import itertools
if TYPE_CHECKING:
    from classes.constraints import Constraint

# Optional matplotlib imports for visual charts
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class Schedule:
    """
    Central class for managing jobs, operations, and resources in a scheduling system.
    
    The Schedule maintains the complete state of a scheduling problem, including all jobs,
    operations, and resources. It provides methods to:
    - Add jobs and resources
    - Schedule operations on resources
    - Validate scheduling constraints (precedence, resource availability, etc.)
    - Visualize schedules with Gantt charts
    
    Attributes:
        name (str): Human-readable name for the schedule
        schedule_id (str): Unique identifier for the schedule
        start_date (datetime): Start date/time of the scheduling period
        end_date (datetime): End date/time of the scheduling period
        jobs (Dict[str, Job]): Dictionary of jobs indexed by job_id
        resources (Dict[str, Resource]): Dictionary of resources indexed by resource_id
        operations (Dict[str, Operation]): Dictionary of all operations indexed by operation_id
    
    Example:
        >>> schedule = Schedule(
        ...     name="Production Schedule - Week 1",
        ...     schedule_id="SCHED_001",
        ...     start_date=datetime(2024, 1, 1, 8, 0),
        ...     end_date=datetime(2024, 1, 5, 17, 0)
        ... )
        >>> schedule.add_resource(machine)
        >>> schedule.add_job(job)
        >>> schedule.schedule_operation("OP_001", "MACHINE_001", datetime(2024, 1, 1, 8, 0))
    """
    
    def __init__(
        self, 
        name: str, 
        schedule_id: str, 
        start_date: datetime, 
        end_date: datetime
    ):
        """
        Initialize a new Schedule.
        
        Args:
            name: Human-readable name for the schedule
            schedule_id: Unique identifier
            start_date: Start of the scheduling period
            end_date: End of the scheduling period
        """
        self.name = name
        self.schedule_id = schedule_id
        self.start_date = start_date
        self.end_date = end_date
        self.jobs: Dict[str, "Job"] = {}
        self.resources: Dict[str, "Resource"] = {}
        self.operations: Dict[str, "Operation"] = {}
        self.constraints: List["Constraint"] = []

    def __str__(self):
        """Return a string representation of the schedule."""
        return f"{self.name} - {self.schedule_id} - {self.start_date} - {self.end_date}"

    def add_job(self, job: "Job"):
        """
        Add a job to the schedule.
        
        This also registers all of the job's operations in the schedule's operation
        dictionary for easy lookup.
        
        Args:
            job: The job to add
            
        Example:
            >>> job = Job("JOB_001", operations, {"customer": "ABC Corp"})
            >>> schedule.add_job(job)
        """
        self.jobs[job.job_id] = job
        for op in job.operations:
            self.operations[op.operation_id] = op

    def add_resource(self, resource: "Resource"):
        """
        Add a resource to the schedule.
        
        Resources must be added before operations can be scheduled on them.
        
        Args:
            resource: The resource to add
            
        Example:
            >>> resource = Resource("MACHINE_001", "machining", "CNC Machine 1")
            >>> schedule.add_resource(resource)
        """
        self.resources[resource.resource_id] = resource

    def add_constraint(self, constraint: "Constraint"):
        """
        Add a scheduling constraint.
        """
        self.constraints.append(constraint)

    def clear_constraints(self):
        """
        Remove all scheduling constraints.
        """
        self.constraints.clear()

    def _constraints_allow(
        self, operation: "Operation", resource: "Resource", start_ts: float, end_ts: float
    ) -> bool:
        for constraint in self.constraints:
            if not constraint.is_feasible(self, operation, resource, start_ts, end_ts):
                return False
        return True

    def _apply_constraints_earliest_start(
        self, operation: "Operation", resource: "Resource", earliest_start: float
    ) -> float:
        adjusted = earliest_start
        for constraint in self.constraints:
            adjusted = max(
                adjusted, constraint.adjust_earliest_start(self, operation, resource, adjusted)
            )
        return adjusted

    def _get_operation_requirements(self, operation: "Operation") -> List[dict]:
        """
        Return normalized resource requirements for an operation.
        """
        return operation.get_resource_requirements()

    def _build_assigned_resources(self, requirements: List[dict], assignment_ids: List[str]) -> dict:
        assigned = {}
        for req, resource_id in zip(requirements, assignment_ids):
            resource_type = req["resource_type"]
            if resource_type in assigned:
                if isinstance(assigned[resource_type], list):
                    assigned[resource_type].append(resource_id)
                else:
                    assigned[resource_type] = [assigned[resource_type], resource_id]
            else:
                assigned[resource_type] = resource_id
        return assigned

    def _find_earliest_slot_for_assignment(
        self,
        operation: "Operation",
        assignment_ids: List[str],
        earliest_start: float,
    ) -> float:
        t = earliest_start
        while True:
            starts = []
            for resource_id in assignment_ids:
                resource = self.resources.get(resource_id)
                if not resource:
                    raise KeyError(f"Resource {resource_id} not found")
                start_i = self._find_earliest_slot(resource, operation.duration, t, operation)
                starts.append(start_i)
            t_next = max(starts)
            if t_next == t:
                return t
            t = t_next

    def _find_earliest_slot_any_resource(
        self, operation: "Operation", earliest_start: float
    ) -> tuple:
        """
        Find the earliest feasible slot across all possible resource assignments.
        """
        requirements = self._get_operation_requirements(operation)
        if not requirements:
            raise ValueError(f"Operation {operation.operation_id} has no resource requirements")

        candidates = []
        for req in requirements:
            candidates.append(req["possible_resource_ids"])

        best_start = None
        best_assignment = None
        original_assigned = dict(operation.assigned_resources)
        for assignment in itertools.product(*candidates):
            valid = True
            for req, resource_id in zip(requirements, assignment):
                resource = self.resources.get(resource_id)
                if not resource or resource.resource_type != req["resource_type"]:
                    valid = False
                    break
            if not valid:
                continue

            operation.assigned_resources = self._build_assigned_resources(
                requirements, list(assignment)
            )
            start_ts = self._find_earliest_slot_for_assignment(
                operation, list(assignment), earliest_start
            )
            if best_start is None or start_ts < best_start:
                best_start = start_ts
                best_assignment = list(assignment)
                if best_start == earliest_start:
                    break

        operation.assigned_resources = original_assigned

        if best_start is None:
            raise RuntimeError(f"No available resource found for {operation.operation_id}")

        assigned_resources = self._build_assigned_resources(requirements, best_assignment)
        return best_start, assigned_resources

    def _find_earliest_slot(
        self,
        resource: "Resource",
        duration: float,
        earliest_start: float,
        operation: Optional["Operation"] = None,
    ) -> float:
        """
        Find the earliest start time (timestamp) on a resource that fits duration.
        """
        t = earliest_start
        while True:
            if operation:
                adjusted = self._apply_constraints_earliest_start(operation, resource, t)
                if adjusted > t:
                    t = adjusted
                    continue
            # Respect availability windows if defined
            if resource.availability_windows:
                window_found = False
                for window_start, window_end in resource.availability_windows:
                    if t < window_start:
                        t = window_start
                    if t + duration <= window_end:
                        window_found = True
                        break
                    t = window_end
                if not window_found:
                    raise RuntimeError(
                        f"No availability window can fit duration on {resource.resource_id}"
                    )

            # Find previous and next operations around time t
            prev_op = None
            next_op = None
            for scheduled_op in resource.schedule:
                if scheduled_op.start_time < t:
                    prev_op = scheduled_op
                    continue
                next_op = scheduled_op
                break

            # Overlap with previous operation
            if prev_op and prev_op.end_time > t:
                t = prev_op.end_time
                continue

            # Check conflict with next operation (including changeover before it)
            if next_op:
                if t + duration > next_op.start_time:
                    t = next_op.end_time
                    continue

            if operation and not self._constraints_allow(operation, resource, t, t + duration):
                adjusted = self._apply_constraints_earliest_start(operation, resource, t + 1)
                if adjusted <= t:
                    adjusted = t + 1
                t = adjusted
                continue

            return t


    def _find_earliest_no_wait_start(
        self, operations: List["Operation"], earliest_start: float
    ) -> tuple:
        """
        Find the earliest start time for a chain of operations with no-wait between them.
        """
        t = earliest_start
        while True:
            shifted = False
            elapsed = 0.0
            chosen_assignments = []
            for op in operations:
                start_i = t + elapsed
                start_i_feasible, assigned_resources = self._find_earliest_slot_any_resource(
                    op, start_i
                )
                if start_i_feasible != start_i:
                    t += start_i_feasible - start_i
                    shifted = True
                    break
                chosen_assignments.append(assigned_resources)
                elapsed += op.duration
            if not shifted:
                return t, chosen_assignments

    def schedule_job_template(
        self,
        job_template: "JobTemplate",
        instance_id: str,
        start_time: datetime,
    ) -> "Job":
        """
        Instantiate a JobTemplate and schedule its operations.

        If a BlockingConstraint is present, operations are scheduled back-to-back with
        no wait time between them (useful when the job cannot leave a resource until
        the next step is ready). Otherwise, each operation is scheduled as early as
        possible after its predecessors complete.
        """
        job = job_template.instantiate(instance_id)
        self.add_job(job)

        blocking = self._has_blocking_constraint()
        earliest_start = start_time.timestamp()

        if blocking:
            start_ts, chosen_assignments = self._find_earliest_no_wait_start(
                job.operations, earliest_start
            )
            elapsed = 0.0
            for op, assigned_resources in zip(job.operations, chosen_assignments):
                op_start = start_ts + elapsed
                scheduled = self.schedule_operation_multi(
                    op.operation_id,
                    assigned_resources,
                    datetime.fromtimestamp(op_start),
                )
                if not scheduled:
                    raise RuntimeError(f"Failed to schedule {op.operation_id} at {op_start}")
                elapsed += op.duration
            return job

        for op in job.operations:
            earliest = earliest_start
            if op.precedence:
                earliest = max(earliest, max(self.operations[p].end_time for p in op.precedence))
            start_ts, assigned_resources = self._find_earliest_slot_any_resource(op, earliest)
            scheduled = self.schedule_operation_multi(
                op.operation_id,
                assigned_resources,
                datetime.fromtimestamp(start_ts),
            )
            if not scheduled:
                raise RuntimeError(f"Failed to schedule {op.operation_id} at {start_ts}")

        return job

    def _has_blocking_constraint(self) -> bool:
        from classes.constraints import BlockingConstraint

        return any(isinstance(c, BlockingConstraint) for c in self.constraints)

    def schedule_operation(self, operation_id: str, resource_id: str, start_time: datetime) -> bool:
        """
        Schedule an operation on a specific resource at a specific time.
        
        This method performs comprehensive validation before scheduling:
        1. Operation and resource exist
        2. Resource type matches operation requirements
        3. Resource is in the operation's allowed resource list
        4. Resource is available during the time window
        5. All precedence constraints are satisfied
        
        If scheduling fails validation or availability checks, the operation remains
        unscheduled and the method returns False. If an error condition is detected
        (wrong types, missing entities), an exception is raised.
        
        Args:
            operation_id: ID of the operation to schedule
            resource_id: ID of the resource to schedule it on
            start_time: When the operation should start (datetime object)
            
        Returns:
            bool: True if scheduling succeeded, False if resource was not available
                  or precedence constraints were not met
                  
        Raises:
            KeyError: If operation_id or resource_id doesn't exist
            ValueError: If resource type doesn't match or resource not in allowed list
            
        Example:
            >>> start = datetime(2024, 1, 1, 8, 0)
            >>> success = schedule.schedule_operation("OP_001", "MACHINE_001", start)
            >>> if success:
            ...     print("Operation scheduled successfully")
        """
        # Validate operation exists
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")

        # Validate resource exists
        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")

        op = self.operations[operation_id]
        resource = self.resources[resource_id]

        requirements = self._get_operation_requirements(op)
        if len(requirements) > 1:
            raise ValueError(
                f"Operation {operation_id} has multiple resource requirements. "
                "Use schedule_operation_multi."
            )

        if len(requirements) == 1:
            req = requirements[0]
            req_type = req["resource_type"]
            req_ids = req["possible_resource_ids"]
        else:
            req_type = op.resource_type
            req_ids = op.possible_resource_ids

        # Validate resource type compatibility
        if req_type and resource.resource_type != req_type:
            raise ValueError(
                f"Resource with type {resource.resource_type} is not allowed "
                f"for operation with type {req_type}"
            )

        # Validate resource is in the operation's allowed resource list
        if req_ids and resource_id not in req_ids:
            raise ValueError(f"Resource {resource_id} is not allowed for operation {operation_id}")

        # Convert datetime to timestamp for internal calculations
        start_timestamp = start_time.timestamp()
        end_timestamp = start_timestamp + op.duration

        # Check resource availability
        if not resource.is_available(start_timestamp, end_timestamp):
            return False

        # Enforce custom constraints
        if not self._constraints_allow(op, resource, start_timestamp, end_timestamp):
            return False
        
        # Verify all precedence constraints are satisfied
        # All predecessor operations must be completed before this one can start
        for pred_op_id in op.precedence:
            pred_op = self.operations.get(pred_op_id)
            if not pred_op or pred_op.end_time is None or pred_op.end_time > start_timestamp:
                return False  # Predecessor not completed yet
                
        # All validations passed - assign scheduling information to the operation
        op.resource_id = resource_id
        op.start_time = start_timestamp
        op.end_time = end_timestamp
        if req_type:
            op.assigned_resources = {req_type: resource_id}

        # Add operation to the resource's schedule
        success = resource.add_operation(op)
        if not success:
            # Rollback if adding to resource failed
            op.resource_id = None
            op.start_time = None
            op.end_time = None
            return False

        return True

    def schedule_operation_multi(
        self, operation_id: str, assigned_resources: dict, start_time: datetime
    ) -> bool:
        """
        Schedule an operation that requires multiple resources at the same time.
        """
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")

        op = self.operations[operation_id]
        requirements = self._get_operation_requirements(op)
        if not requirements:
            raise ValueError(f"Operation {operation_id} has no resource requirements")

        # Build flat list of assigned ids in requirement order
        assignment_ids = []
        list_positions = {}
        for req in requirements:
            req_type = req["resource_type"]
            if req_type not in assigned_resources:
                raise ValueError(f"Missing assigned resource for type {req_type}")
            assigned = assigned_resources[req_type]
            if isinstance(assigned, list):
                if not assigned:
                    raise ValueError(f"No assigned resources provided for type {req_type}")
                idx = list_positions.get(req_type, 0)
                if idx >= len(assigned):
                    raise ValueError(f"Not enough assigned resources provided for type {req_type}")
                assignment_ids.append(assigned[idx])
                list_positions[req_type] = idx + 1
            else:
                assignment_ids.append(assigned)

        # Validate resources exist and types match
        resources = []
        for req, resource_id in zip(requirements, assignment_ids):
            if resource_id not in self.resources:
                raise KeyError(f"Resource {resource_id} not found")
            resource = self.resources[resource_id]
            if resource.resource_type != req["resource_type"]:
                raise ValueError(
                    f"Resource with type {resource.resource_type} is not allowed "
                    f"for requirement type {req['resource_type']}"
                )
            if resource_id not in req["possible_resource_ids"]:
                raise ValueError(f"Resource {resource_id} is not allowed for operation {operation_id}")
            resources.append(resource)

        # Convert datetime to timestamp for internal calculations
        start_timestamp = start_time.timestamp()
        end_timestamp = start_timestamp + op.duration

        # Check resource availability and constraints
        original_assigned = dict(op.assigned_resources)
        op.assigned_resources = assigned_resources
        for resource in resources:
            if not resource.is_available(start_timestamp, end_timestamp):
                op.assigned_resources = original_assigned
                return False
            if not self._constraints_allow(op, resource, start_timestamp, end_timestamp):
                op.assigned_resources = original_assigned
                return False

        # Verify all precedence constraints are satisfied
        for pred_op_id in op.precedence:
            pred_op = self.operations.get(pred_op_id)
            if not pred_op or pred_op.end_time is None or pred_op.end_time > start_timestamp:
                return False

        # Assign scheduling info
        op.resource_id = assignment_ids[0]
        op.start_time = start_timestamp
        op.end_time = end_timestamp
        op.assigned_resources = self._build_assigned_resources(requirements, assignment_ids)

        # Add operation to each resource schedule
        for resource in resources:
            if not resource.add_operation(op):
                # Rollback if any add fails
                for res in resources:
                    res.remove_operation(op)
                op.unschedule()
                return False

        return True

    def unschedule_operation(self, operation_id: str):
        """
        Remove an operation from its scheduled resource.
        
        This resets the operation to an unscheduled state, clearing its start_time,
        end_time, and resource_id. If the operation isn't currently scheduled, this
        method does nothing.
        
        Args:
            operation_id: ID of the operation to unschedule
            
        Raises:
            KeyError: If operation_id doesn't exist
            
        Example:
            >>> schedule.unschedule_operation("OP_001")
            >>> # Operation is now unscheduled and can be rescheduled
        """
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")
            
        op = self.operations[operation_id]
        
        # If already unscheduled, nothing to do
        if not op.is_scheduled():
            return

        # Remove from all assigned resources
        for res_id in op.get_assigned_resource_ids():
            resource = self.resources.get(res_id)
            if resource:
                resource.remove_operation(op)

        # Reset scheduling information
        op.resource_id = None
        op.start_time = None
        op.end_time = None
    
    def get_scheduled_operations(self) -> Dict[str, "Operation"]:
        """
        Get all operations that have been scheduled.
        
        Returns:
            Dict[str, Operation]: Dictionary of scheduled operations indexed by operation_id
            
        Example:
            >>> scheduled = schedule.get_scheduled_operations()
            >>> print(f"{len(scheduled)} operations scheduled")
        """
        return {op_id: op for op_id, op in self.operations.items() if op.is_scheduled()}
    
    def get_unscheduled_operations(self) -> Dict[str, "Operation"]:
        """
        Get all operations that have not been scheduled yet.
        
        Returns:
            Dict[str, Operation]: Dictionary of unscheduled operations indexed by operation_id
            
        Example:
            >>> unscheduled = schedule.get_unscheduled_operations()
            >>> for op_id, op in unscheduled.items():
            ...     print(f"Need to schedule: {op_id}")
        """
        return {op_id: op for op_id, op in self.operations.items() if not op.is_scheduled()}
    
    def get_job_completion_time(self, job_id: str) -> Optional[float]:
        """
        Get the completion time of a job (when its last operation finishes).
        
        Args:
            job_id: ID of the job
            
        Returns:
            float: Unix timestamp when job completes, or None if job not found or not fully scheduled
            
        Raises:
            KeyError: If job_id doesn't exist
            
        Example:
            >>> completion = schedule.get_job_completion_time("JOB_001")
            >>> if completion:
            ...     print(f"Job completes at {datetime.fromtimestamp(completion)}")
        """
        if job_id not in self.jobs:
            raise KeyError(f"Job {job_id} not found")
        
        return self.jobs[job_id].get_end_time()
    
    def get_makespan(self) -> Optional[float]:
        """
        Get the overall makespan (time from first operation to last operation).
        
        Returns:
            float: Total time in seconds from start to finish, or None if no operations scheduled
            
        Example:
            >>> makespan = schedule.get_makespan()
            >>> if makespan:
            ...     print(f"Schedule takes {makespan / 3600:.1f} hours")
        """
        scheduled = list(self.get_scheduled_operations().values())
        if not scheduled:
            return None
        
        earliest = min(op.start_time for op in scheduled)
        latest = max(op.end_time for op in scheduled)
        return latest - earliest
    
    def get_resources_by_type(self, resource_type: str) -> Dict[str, "Resource"]:
        """
        Get all resources of a specific type.
        
        Args:
            resource_type: The resource type to filter by
            
        Returns:
            Dict[str, Resource]: Dictionary of resources of this type
            
        Example:
            >>> machines = schedule.get_resources_by_type("machining")
            >>> print(f"Found {len(machines)} machining resources")
        """
        return {r_id: r for r_id, r in self.resources.items() if r.resource_type == resource_type}
    
    def find_available_resources(self, operation_id: str, start_time: datetime) -> List[str]:
        """
        Find which resources can perform an operation at a specific time.
        
        This checks both resource compatibility and availability.
        
        Args:
            operation_id: ID of the operation
            start_time: Proposed start time (datetime object)
            
        Returns:
            List[str]: List of resource IDs that can perform this operation at this time
            
        Raises:
            KeyError: If operation_id doesn't exist
            
        Example:
            >>> available = schedule.find_available_resources("OP_001", datetime(2024, 1, 1, 8, 0))
            >>> print(f"Can use resources: {available}")
        """
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")
        
        op = self.operations[operation_id]
        requirements = self._get_operation_requirements(op)
        if len(requirements) != 1:
            raise ValueError(
                "Operation has multiple resource requirements. "
                "Use find_available_resource_sets instead."
            )
        start_ts = start_time.timestamp()
        end_ts = start_ts + op.duration
        
        available = []
        for resource_id in requirements[0]["possible_resource_ids"]:
            resource = self.resources.get(resource_id)
            if resource and resource.is_available(start_ts, end_ts):
                if not self._constraints_allow(op, resource, start_ts, end_ts):
                    continue
                # Also check precedence constraints
                if op.can_start_at(start_ts, self.operations):
                    available.append(resource_id)
        
        return available

    def find_available_resource_sets(
        self, operation_id: str, start_time: datetime
    ) -> List[dict]:
        """
        Find feasible resource assignments for a multi-resource operation at a time.
        """
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")

        op = self.operations[operation_id]
        requirements = self._get_operation_requirements(op)
        if not requirements:
            raise ValueError(f"Operation {operation_id} has no resource requirements")

        start_ts = start_time.timestamp()
        end_ts = start_ts + op.duration

        candidates = [req["possible_resource_ids"] for req in requirements]
        feasible = []
        for assignment in itertools.product(*candidates):
            valid = True
            for req, resource_id in zip(requirements, assignment):
                resource = self.resources.get(resource_id)
                if not resource or resource.resource_type != req["resource_type"]:
                    valid = False
                    break
                if not resource.is_available(start_ts, end_ts):
                    valid = False
                    break
                if not self._constraints_allow(op, resource, start_ts, end_ts):
                    valid = False
                    break
            if not valid:
                continue
            if not op.can_start_at(start_ts, self.operations):
                continue
            feasible.append(self._build_assigned_resources(requirements, list(assignment)))

        return feasible

    def get_resource_used_time(
        self,
        resource_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Get total busy time (seconds) for a resource in a time window.
        """
        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")

        resource = self.resources[resource_id]
        if not resource.schedule:
            return 0.0

        start_ts = start_time.timestamp() if start_time else resource.schedule[0].start_time
        end_ts = end_time.timestamp() if end_time else resource.schedule[-1].end_time

        if end_ts <= start_ts:
            return 0.0

        busy_time = 0.0
        for op in resource.schedule:
            if op.end_time <= start_ts or op.start_time >= end_ts:
                continue
            overlap_start = max(start_ts, op.start_time)
            overlap_end = min(end_ts, op.end_time)
            busy_time += overlap_end - overlap_start

        return busy_time

    def get_resource_total_time(
        self,
        resource_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Get total elapsed time (seconds) on a resource, including idle gaps.
        """
        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")

        resource = self.resources[resource_id]
        if not resource.schedule:
            return 0.0

        start_ts = start_time.timestamp() if start_time else resource.schedule[0].start_time
        end_ts = end_time.timestamp() if end_time else resource.schedule[-1].end_time

        if end_ts <= start_ts:
            return 0.0

        return end_ts - start_ts

    def get_total_operational_time(self) -> float:
        """
        Get total operational time (seconds) from first start to last end.
        """
        scheduled_ops = list(self.get_scheduled_operations().values())
        if not scheduled_ops:
            return 0.0

        earliest = min(op.start_time for op in scheduled_ops)
        latest = max(op.end_time for op in scheduled_ops)
        if latest <= earliest:
            return 0.0
        return latest - earliest
    
    def validate_schedule(self) -> Dict[str, List[str]]:
        """
        Validate the schedule for conflicts and constraint violations.
        
        Checks for:
        - Resource conflicts (double-booking)
        - Precedence violations
        - Resource type mismatches
        
        Returns:
            Dict[str, List[str]]: Dictionary of validation issues, empty if valid
            
        Example:
            >>> issues = schedule.validate_schedule()
            >>> if issues:
            ...     print("Schedule has issues:", issues)
            >>> else:
            ...     print("Schedule is valid!")
        """
        issues = {
            "resource_conflicts": [],
            "precedence_violations": [],
            "type_mismatches": []
        }
        
        # Check for resource conflicts
        for resource_id, resource in self.resources.items():
            for i in range(len(resource.schedule) - 1):
                op1 = resource.schedule[i]
                op2 = resource.schedule[i + 1]
                if op1.end_time > op2.start_time:
                    issues["resource_conflicts"].append(
                        f"Resource {resource_id}: {op1.operation_id} overlaps with {op2.operation_id}"
                    )
        
        # Check precedence violations
        for op_id, op in self.operations.items():
            if not op.is_scheduled():
                continue
            
            for pred_id in op.precedence:
                pred_op = self.operations.get(pred_id)
                if not pred_op or not pred_op.is_scheduled():
                    issues["precedence_violations"].append(
                        f"Operation {op_id}: precedence {pred_id} not scheduled"
                    )
                elif pred_op.end_time > op.start_time:
                    issues["precedence_violations"].append(
                        f"Operation {op_id} starts before precedence {pred_id} completes"
                    )
        
        # Check resource type mismatches
        for op_id, op in self.operations.items():
            if not op.is_scheduled():
                continue

            for res_id in op.get_assigned_resource_ids():
                resource = self.resources.get(res_id)
                if not resource:
                    continue
                requirements = op.get_resource_requirements()
                if not requirements:
                    continue
                allowed_types = {req["resource_type"] for req in requirements}
                if resource.resource_type not in allowed_types:
                    issues["type_mismatches"].append(
                        f"Operation {op_id} requires {sorted(allowed_types)} but scheduled on {resource.resource_type}"
                    )
        
        # Remove empty categories
        return {k: v for k, v in issues.items() if v}
    
    def clear_all_schedules(self):
        """
        Unschedule all operations and clear all resource schedules.
        
        This resets the entire schedule to an unscheduled state while keeping
        all jobs, operations, and resources defined.
        
        Example:
            >>> schedule.clear_all_schedules()
            >>> assert len(schedule.get_scheduled_operations()) == 0
        """
        # Unschedule all operations
        for op in self.operations.values():
            op.unschedule()
        
        # Clear all resource schedules
        for resource in self.resources.values():
            resource.clear_schedule()
    
    def get_schedule_statistics(self) -> dict:
        """
        Get comprehensive statistics about the schedule.
        
        Returns:
            dict: Dictionary containing various schedule metrics
            
        Example:
            >>> stats = schedule.get_schedule_statistics()
            >>> print(f"Utilization: {stats['avg_resource_utilization']:.1%}")
        """
        scheduled_ops = list(self.get_scheduled_operations().values())
        
        if not scheduled_ops:
            return {
                "total_operations": len(self.operations),
                "scheduled_operations": 0,
                "unscheduled_operations": len(self.operations),
                "total_jobs": len(self.jobs),
                "complete_jobs": 0,
                "total_resources": len(self.resources),
                "makespan_hours": 0,
                "avg_resource_utilization": 0
            }
        
        earliest = min(op.start_time for op in scheduled_ops)
        latest = max(op.end_time for op in scheduled_ops)
        makespan = latest - earliest
        
        # Calculate average resource utilization
        total_util = 0
        for resource in self.resources.values():
            if len(resource.schedule) > 0:
                util = resource.get_utilization(earliest, latest)
                total_util += util
        avg_util = total_util / len(self.resources) if self.resources else 0
        
        complete_jobs = sum(1 for job in self.jobs.values() if job.is_complete())
        
        return {
            "total_operations": len(self.operations),
            "scheduled_operations": len(scheduled_ops),
            "unscheduled_operations": len(self.operations) - len(scheduled_ops),
            "total_jobs": len(self.jobs),
            "complete_jobs": complete_jobs,
            "incomplete_jobs": len(self.jobs) - complete_jobs,
            "total_resources": len(self.resources),
            "makespan_hours": makespan / 3600,
            "avg_resource_utilization": avg_util
        }
    
    def print_schedule_statistics(self):
        """
        Print a formatted summary of schedule statistics.
        
        Example:
            >>> schedule.print_schedule_statistics()
            === Schedule Statistics ===
            Operations: 15 total, 12 scheduled, 3 unscheduled
            ...
        """
        stats = self.get_schedule_statistics()
        
        print("\n=== Schedule Statistics ===")
        print(f"Operations: {stats['total_operations']} total, "
              f"{stats['scheduled_operations']} scheduled, "
              f"{stats['unscheduled_operations']} unscheduled")
        print(f"Jobs: {stats['total_jobs']} total, "
              f"{stats['complete_jobs']} complete, "
              f"{stats['incomplete_jobs']} incomplete")
        print(f"Resources: {stats['total_resources']}")
        print(f"Makespan: {stats['makespan_hours']:.2f} hours")
        print(f"Avg Resource Utilization: {stats['avg_resource_utilization']:.1%}")
        
        # Validation
        issues = self.validate_schedule()
        if issues:
            print("\n[!] Validation Issues Found:")
            for category, problems in issues.items():
                print(f"  {category}:")
                for problem in problems:
                    print(f"    - {problem}")
        else:
            print("\n[OK] Schedule is valid (no conflicts detected)")

    def create_gantt_chart(self):
        """
        Create a text-based Gantt chart representation of the schedule.
        
        This method prints a console-friendly visualization of the schedule showing:
        - Time range of the schedule
        - Operations grouped by job
        - Visual bars representing operation duration
        - Resource assignments
        
        The chart is printed to stdout and suitable for quick visual inspection
        without requiring matplotlib.
        
        Example:
            >>> schedule.create_gantt_chart()
            === Gantt Chart ===
            Schedule: Production Schedule - Week 1
            Time Range: Mon 08:00 - Mon 13:30
            
            JOB_A (ABC Corp - high priority):
              A_MACH: Mon 08:00 |████████| 10:00 [MACHINE_001] (2.0h)
              A_ASSY: Mon 10:00 |████| 11:00 [ASSEMBLY_001] (1.0h)
        """
        print(f"\n=== Gantt Chart ===")
        print(f"Schedule: {self.name}")
        
        # Collect all scheduled operations (dedupe across resources)
        all_operations = {}
        for resource in self.resources.values():
            for operation in resource.schedule:
                all_operations[operation.operation_id] = operation
        all_operations = list(all_operations.values())
        
        if not all_operations:
            print("No operations scheduled")
            return
        
        # Sort chronologically for display
        all_operations.sort(key=lambda op: op.start_time)
        
        # Determine the time range covered by the schedule
        earliest_start = min(op.start_time for op in all_operations)
        latest_end = max(op.end_time for op in all_operations)
        
        earliest_dt = datetime.fromtimestamp(earliest_start)
        latest_dt = datetime.fromtimestamp(latest_end)
        
        print(f"Time Range: {earliest_dt.strftime('%a %H:%M')} - {latest_dt.strftime('%a %H:%M')}")
        print()
        
        # Organize operations by job for grouped display
        jobs_operations = {}
        for operation in all_operations:
            job_id = operation.job_id
            if job_id not in jobs_operations:
                jobs_operations[job_id] = []
            jobs_operations[job_id].append(operation)
        
        # Print Gantt chart for each job
        for job_id in sorted(jobs_operations.keys()):
            job = self.jobs.get(job_id)
            customer = job.metadata.get('customer', 'Unknown') if job else 'Unknown'
            priority = job.metadata.get('priority', 'Unknown') if job else 'Unknown'
            
            print(f"{job_id} ({customer} - {priority} priority):")
            
            operations = jobs_operations[job_id]
            operations.sort(key=lambda op: op.start_time)
            
            for operation in operations:
                start_dt = datetime.fromtimestamp(operation.start_time)
                end_dt = datetime.fromtimestamp(operation.end_time)
                duration_hours = (operation.end_time - operation.start_time) / 3600
                
                # Create visual bar (4 characters per hour of duration)
                # Use ASCII to avoid Windows console encoding issues.
                bar_length = max(1, int(duration_hours * 4))
                bar = "#" * bar_length
                
                resource_ids = operation.get_assigned_resource_ids() or (
                    [operation.resource_id] if operation.resource_id else []
                )
                resource_label = ",".join(resource_ids) if resource_ids else "unassigned"
                print(
                    f"  {operation.operation_id:>8}: {start_dt.strftime('%a %H:%M')} "
                    f"|{bar}| {end_dt.strftime('%H:%M')} "
                    f"[{resource_label}] ({duration_hours:.1f}h)"
                )
            
            print()

    def show_visual_gantt_chart(self):
        """
        Create and display a visual Gantt chart using matplotlib.
        
        This method creates an interactive graphical Gantt chart with:
        - Color-coded operations by job
        - Resources on the y-axis
        - Time on the x-axis
        - Legend showing job details
        - Operation labels on bars
        
        The chart is displayed in a matplotlib window. This requires matplotlib
        to be installed. If matplotlib is not available, an error message is printed.
        
        Returns:
            tuple: (fig, ax) matplotlib figure and axis objects if successful,
                   None if matplotlib is not available or no operations are scheduled
                   
        Example:
            >>> schedule.show_visual_gantt_chart()
            # Opens a matplotlib window with an interactive Gantt chart
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Error: matplotlib is required for visual Gantt charts. Install with: pip install matplotlib")
            return
        
        # Collect all operations with resource context and sort by start time
        all_operations = []
        for resource in self.resources.values():
            for operation in resource.schedule:
                all_operations.append((operation, resource.resource_id))
        
        if not all_operations:
            print("No operations scheduled to display")
            return
        
        # Group operations by job for color coding
        jobs_operations = {}
        for operation, _ in all_operations:
            job_id = operation.job_id
            if job_id not in jobs_operations:
                jobs_operations[job_id] = []
            jobs_operations[job_id].append(operation)
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Define colors for different job types
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
        job_type_colors = {}
        job_type_by_id = {}
        for job_id in sorted(jobs_operations.keys()):
            job = self.jobs.get(job_id)
            job_type = None
            if job:
                job_type = job.metadata.get("job_type") or job.metadata.get("module_type")
            if not job_type:
                job_type = job_id
            job_type_by_id[job_id] = job_type

        for i, job_type in enumerate(sorted(set(job_type_by_id.values()))):
            job_type_colors[job_type] = colors[i % len(colors)]
        
        # Get all resources for y-axis
        resources = list(self.resources.keys())
        resources.sort()
        
        # Create y-position mapping
        y_positions = {resource: i for i, resource in enumerate(resources)}
        
        # Plot operations as colored rectangles
        for operation, resource_id in all_operations:
            start_dt = datetime.fromtimestamp(operation.start_time)
            end_dt = datetime.fromtimestamp(operation.end_time)
            duration = end_dt - start_dt
            
            y_pos = y_positions[resource_id]
            color = job_type_colors[job_type_by_id[operation.job_id]]
            
            # Create rectangle for the operation
            # Convert duration to matplotlib date units (days) for proper x-axis scaling
            duration_days = duration.total_seconds() / (24 * 3600)
            rect = Rectangle(
                (mdates.date2num(start_dt), y_pos - 0.4),  # Position and vertical centering
                duration_days,  # Width (duration)
                0.8,  # Height (leaves space between resources)
                facecolor=color,
                edgecolor='black',
                alpha=0.7
            )
            ax.add_patch(rect)
            
            # Add operation label in the center of the rectangle
            mid_time = start_dt + duration / 2
            # Choose text color based on background brightness (sum of RGB values)
            # Dark backgrounds get white text, light backgrounds get black text
            rgb_sum = sum(int(color[i:i+2], 16) for i in (1, 3, 5))
            text_color = 'white' if rgb_sum < 300 else 'black'
            label = operation.operation_id.split("_")[-1]
            ax.text(
                mdates.date2num(mid_time),
                y_pos,
                label,
                ha='center',
                va='center',
                fontsize=8,
                fontweight='bold',
                color=text_color
            )
        
        # Set up the plot
        ax.set_ylim(-0.5, len(resources) - 0.5)
        ax.set_yticks(range(len(resources)))
        ax.set_yticklabels([f"{res}\n({self.resources[res].resource_name})" for res in resources])
        
        # Format x-axis for time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=30))
        
        # Set time range
        if all_operations:
            earliest_start = min(op.start_time for op, _ in all_operations)
            latest_end = max(op.end_time for op, _ in all_operations)
            start_dt = datetime.fromtimestamp(earliest_start)
            end_dt = datetime.fromtimestamp(latest_end)
            
            # Add some padding
            padding = timedelta(minutes=30)
            ax.set_xlim(
                mdates.date2num(start_dt - padding),
                mdates.date2num(end_dt + padding)
            )
        
        # Customize the plot
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Resources', fontsize=12)
        ax.set_title(f'{self.name}\nGantt Chart - {self.start_date.strftime("%Y-%m-%d")}', fontsize=14, fontweight='bold')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Create legend
        legend_elements = []
        for job_type in sorted(job_type_colors.keys()):
            legend_elements.append(
                Rectangle((0, 0), 1, 1, facecolor=job_type_colors[job_type], alpha=0.7,
                         label=f'{job_type}')
            )
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        # Adjust layout to prevent clipping
        plt.tight_layout()
        
        # Show the plot
        plt.show()
        
        return fig, ax