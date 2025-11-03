"""
Resource class for the scheduling library.

A Resource represents a machine, line, station, or any entity that can perform operations.
Resources maintain their own schedule and availability windows.
"""

from sortedcontainers import SortedList
from typing import Optional, List, Tuple
from operation import Operation


class Resource:
    """
    Represents a resource that can perform operations.
    
    A Resource is any entity that can execute operations (e.g., machines, workstations,
    personnel). Resources have a type that must match the operation's required resource type.
    They maintain a schedule of assigned operations and can have availability windows that
    restrict when they can work.
    
    Attributes:
        resource_id (str): Unique identifier for the resource
        resource_type (str): Type of resource (e.g., "machining", "assembly")
        resource_name (str): Human-readable name for the resource
        availability_windows (List[Tuple[float, float]]): List of time ranges when the resource
            is available, represented as (start_timestamp, end_timestamp) tuples
        schedule (SortedList): Ordered list of operations scheduled on this resource,
            automatically sorted by start_time for efficient conflict detection
    
    Example:
        >>> # Create a machine that works 8 AM to 5 PM
        >>> work_start = datetime(2024, 1, 1, 8, 0).timestamp()
        >>> work_end = datetime(2024, 1, 1, 17, 0).timestamp()
        >>> resource = Resource(
        ...     resource_id="MACHINE_001",
        ...     resource_type="machining",
        ...     resource_name="CNC Machine 1",
        ...     availability_windows=[(work_start, work_end)]
        ... )
    """
    
    def __init__(
        self,
        resource_id: str,
        resource_type: str,
        resource_name: str,
        availability_windows: Optional[List[Tuple[float, float]]] = None,
    ):
        """
        Initialize a new Resource.
        
        Args:
            resource_id: Unique identifier for this resource
            resource_type: Type of resource (must match operation resource types)
            resource_name: Human-readable name
            availability_windows: Optional list of (start, end) timestamp tuples
                representing when the resource is available
        """
        self.resource_id = resource_id  
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.availability_windows = availability_windows or []
        # SortedList maintains operations in chronological order for efficient conflict detection
        self.schedule = SortedList()

    def is_available(self, start: float, end: float) -> bool:
        """
        Check if the resource is available during the specified time range.
        
        This method performs two checks:
        1. If availability windows are defined, ensures [start, end) falls within one
        2. Checks for conflicts with already scheduled operations using binary search
        
        The algorithm uses binary search (O(log n)) to efficiently find potential conflicts
        among scheduled operations, rather than checking all operations (O(n)).
        
        Args:
            start: Start timestamp (Unix timestamp)
            end: End timestamp (Unix timestamp)
            
        Returns:
            bool: True if the resource is available for the entire [start, end) interval,
                  False if there's a conflict or the time is outside availability windows
        
        Example:
            >>> work_start = datetime(2024, 1, 1, 8, 0).timestamp()
            >>> work_end = datetime(2024, 1, 1, 10, 0).timestamp()
            >>> resource.is_available(work_start, work_end)
            True
        """
        # Check if the requested time falls within availability windows
        if self.availability_windows:
            # The entire [start, end) interval must lie within at least one availability window
            if not any(ws <= start and end <= we for ws, we in self.availability_windows):
                return False

        # If no operations are scheduled, the resource is available
        if not self.schedule:
            return True

        # Use binary search to find potential overlapping operations
        # Create a dummy operation to find where this time slot would fit in the schedule
        dummy_op = Operation("dummy", "dummy", 0, self.resource_type, start_time=start, end_time=end)
        pos = self.schedule.bisect_left(dummy_op)

        # Check the operation immediately before the insertion point
        # If it ends after our start time, there's an overlap
        if pos > 0:
            prev_op = self.schedule[pos - 1]
            if prev_op.end_time > start:
                return False

        # Check the operation at the insertion point
        # If it starts before our end time, there's an overlap
        if pos < len(self.schedule):
            next_op = self.schedule[pos]
            if next_op.start_time < end:
                return False

        # No conflicts found
        return True

    def add_operation(self, operation: Operation) -> bool:
        """
        Add an operation to this resource's schedule.
        
        This method validates that:
        1. The operation has scheduling information (start_time and end_time)
        2. The operation's resource type matches this resource's type
        3. The resource is available during the operation's time slot
        
        Args:
            operation: The operation to add to the schedule
            
        Returns:
            bool: True if the operation was successfully added, False if the time slot
                  is not available
                  
        Raises:
            ValueError: If the operation is missing scheduling info or has an incompatible
                       resource type
                       
        Example:
            >>> operation = Operation("OP_001", "JOB_001", 3600, "machining")
            >>> operation.start_time = datetime(2024, 1, 1, 8, 0).timestamp()
            >>> operation.end_time = datetime(2024, 1, 1, 9, 0).timestamp()
            >>> success = resource.add_operation(operation)
        """
        # Validate operation has scheduling information
        if not operation.start_time or not operation.end_time:
            raise ValueError("Operation must have start_time and end_time before scheduling")

        # Validate resource type compatibility
        if operation.resource_type != self.resource_type:
            raise ValueError(
                f"Operation with resource type {operation.resource_type} can't be scheduled "
                f"on resource {self.resource_name} with type {self.resource_type}"
            )

        # Check for scheduling conflicts
        if not self.is_available(operation.start_time, operation.end_time):
            return False

        # Add to schedule (SortedList automatically maintains sort order)
        self.schedule.add(operation)
        return True

    def remove_operation(self, operation: Operation):
        """
        Remove an operation from this resource's schedule.
        
        This is typically used when unscheduling an operation or when rescheduling
        operations. Uses discard (not remove) so it won't raise an error if the
        operation isn't in the schedule.
        
        Args:
            operation: The operation to remove from the schedule
            
        Example:
            >>> resource.remove_operation(operation)
        """
        self.schedule.discard(operation)