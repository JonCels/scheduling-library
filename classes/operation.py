"""
Operation class for the scheduling library.

An Operation represents a single step in a job that must be performed on a specific
resource type for a defined duration.
"""

from typing import List, Optional


class Operation:
    """
    Represents a single operation within a job that needs to be scheduled.
    
    An Operation is the atomic unit of work in the scheduling system. Each operation
    must be performed on a specific type of resource and has a defined duration.
    Operations can have precedence constraints (must wait for other operations to
    complete) and can only be assigned to compatible resources.
    
    Attributes:
        operation_id (str): Unique identifier for the operation
        job_id (str): ID of the job this operation belongs to
        duration (float): Duration of the operation in seconds
        resource_type (str): Type of resource required (e.g., "machining", "assembly")
        possible_resource_ids (List[str]): List of specific resources that can perform this operation
        precedence (List[str]): List of operation IDs that must complete before this one
        metadata (dict): Optional dictionary for additional operation information
        start_time (float): Scheduled start time as Unix timestamp (None if unscheduled)
        end_time (float): Scheduled end time as Unix timestamp (None if unscheduled)
        resource_id (str): ID of the resource this operation is scheduled on (None if unscheduled)
    
    Example:
        >>> op = Operation(
        ...     operation_id="OP_001",
        ...     job_id="JOB_001",
        ...     duration=3600.0,  # 1 hour in seconds
        ...     resource_type="machining",
        ...     possible_resource_ids=["MACHINE_001", "MACHINE_002"],
        ...     precedence=["OP_000"],  # Must wait for OP_000 to complete
        ...     metadata={"description": "Machine part A"}
        ... )
    """
    
    def __init__(
        self,
        operation_id: str,
        job_id: str,
        duration: float,
        resource_type: str,
        possible_resource_ids: Optional[List[str]] = None,
        precedence: Optional[List[str]] = None,
        metadata: Optional[dict] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        resource_id: Optional[str] = None,
    ):
        """
        Initialize a new Operation.
        
        Args:
            operation_id: Unique identifier for this operation
            job_id: ID of the parent job
            duration: Duration in seconds
            resource_type: Type of resource required (must match a resource's type)
            possible_resource_ids: List of specific resource IDs that can perform this operation
            precedence: List of operation IDs that must complete before this can start
            metadata: Optional dictionary for additional operation information
            start_time: Scheduled start time as Unix timestamp (set during scheduling)
            end_time: Scheduled end time as Unix timestamp (set during scheduling)
            resource_id: ID of assigned resource (set during scheduling)
        """
        self.operation_id = operation_id
        self.job_id = job_id
        self.duration = duration
        self.resource_type = resource_type  # e.g., "machining", "assembly", "painting"
        self.possible_resource_ids = possible_resource_ids or []
        self.precedence = precedence or []  # Operations that must complete first
        self.metadata = metadata or {}
        self.start_time = start_time
        self.end_time = end_time
        self.resource_id = resource_id

    def is_scheduled(self) -> bool:
        """
        Check if this operation has been scheduled.
        
        An operation is considered scheduled if it has both a start_time and end_time.
        
        Returns:
            bool: True if the operation is scheduled, False otherwise
        """
        return self.start_time is not None and self.end_time is not None

    def unschedule(self):
        """
        Clear scheduling information from this operation.
        
        This resets the operation to an unscheduled state without removing it
        from any resource's schedule. Use Schedule.unschedule_operation() instead
        if you want to properly remove it from a resource.
        
        Example:
            >>> operation.unschedule()
            >>> assert operation.start_time is None
        """
        self.start_time = None
        self.end_time = None
        self.resource_id = None

    def can_start_at(self, time: float, operations_dict: dict = None) -> bool:
        """
        Check if this operation can start at the specified time based on precedence.
        
        This verifies that all predecessor operations in the precedence list have
        completed before the specified time.
        
        Args:
            time: Unix timestamp to check
            operations_dict: Dictionary of operation_id -> Operation for looking up precedence.
                           If None, assumes no precedence constraints.
            
        Returns:
            bool: True if all precedence constraints are satisfied, False otherwise
            
        Example:
            >>> # Check if operation can start at 8 AM
            >>> can_start = operation.can_start_at(start_time.timestamp(), schedule.operations)
        """
        if not self.precedence:
            return True
        
        if operations_dict is None:
            # No way to check precedence without operation dictionary
            return True
        
        for pred_id in self.precedence:
            pred_op = operations_dict.get(pred_id)
            if not pred_op:
                return False  # Precedence operation doesn't exist
            if not pred_op.is_scheduled():
                return False  # Precedence operation not scheduled yet
            if pred_op.end_time > time:
                return False  # Precedence operation ends after our start time
        
        return True

    def get_duration_hours(self) -> float:
        """
        Get the operation duration in hours.
        
        Returns:
            float: Duration in hours
            
        Example:
            >>> operation.duration = 3600  # 1 hour in seconds
            >>> operation.get_duration_hours()
            1.0
        """
        return self.duration / 3600

    def __lt__(self, other):
        """
        Compare operations for sorting by start_time.
        
        This enables sorting operations chronologically. Unscheduled operations
        (with start_time=None) are treated as coming after all scheduled operations.
        
        Args:
            other (Operation): Another operation to compare with
            
        Returns:
            bool: True if this operation starts before the other
        """
        # Unscheduled operations come last when sorting
        if self.start_time is None:
            return False

        if other.start_time is None:
            return True

        return self.start_time < other.start_time
    
    def __repr__(self):
        """
        Return a detailed string representation of the operation.
        
        Returns:
            str: String representation with key attributes
        """
        status = "scheduled" if self.is_scheduled() else "unscheduled"
        return (f"Operation(id={self.operation_id}, job={self.job_id}, "
                f"type={self.resource_type}, duration={self.get_duration_hours():.1f}h, "
                f"status={status})")