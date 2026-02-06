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
    
    def get_operation_at(self, time: float) -> Optional[Operation]:
        """
        Get the operation running at a specific time.
        
        Args:
            time: Unix timestamp to check
            
        Returns:
            Operation: The operation running at this time, or None if resource is idle
            
        Example:
            >>> op = resource.get_operation_at(datetime(2024, 1, 1, 10, 0).timestamp())
            >>> if op:
            ...     print(f"Resource is running {op.operation_id}")
        """
        for op in self.schedule:
            if op.start_time <= time < op.end_time:
                return op
        return None
    
    def get_next_available_time(self, duration: float, after: float = 0) -> Optional[float]:
        """
        Find the next time slot where this resource can fit an operation of given duration.
        
        This method searches for gaps in the schedule (or after all scheduled operations)
        where an operation of the specified duration can fit.
        
        Args:
            duration: Duration in seconds of the operation to fit
            after: Unix timestamp - start searching after this time (default: 0)
            
        Returns:
            float: Unix timestamp of next available start time, or None if no availability
                  windows are defined and the resource has operations scheduled
            
        Example:
            >>> # Find when we can schedule a 2-hour operation
            >>> next_time = resource.get_next_available_time(7200, current_time.timestamp())
            >>> if next_time:
            ...     print(f"Can schedule at {datetime.fromtimestamp(next_time)}")
        """
        # If no availability windows defined, find the first gap after 'after' time
        if not self.availability_windows:
            if not self.schedule:
                return after
            
            # Find first gap that fits after the specified time
            for i in range(len(self.schedule)):
                if i == 0:
                    # Check before first operation
                    if self.schedule[0].start_time >= after + duration:
                        return max(after, 0)
                
                # Check gap between operations
                if i < len(self.schedule) - 1:
                    gap_start = max(after, self.schedule[i].end_time)
                    gap_end = self.schedule[i + 1].start_time
                    if gap_end - gap_start >= duration:
                        return gap_start
            
            # Can fit after all operations
            if self.schedule:
                return max(after, self.schedule[-1].end_time)
            return after
        
        # With availability windows, check each window
        for window_start, window_end in self.availability_windows:
            search_start = max(after, window_start)
            
            if search_start + duration > window_end:
                continue  # Duration doesn't fit in this window
            
            # Check if we can fit at the beginning of the window
            if self.is_available(search_start, search_start + duration):
                return search_start
            
            # Check gaps within this window
            for i, op in enumerate(self.schedule):
                if op.start_time >= window_end:
                    break  # Past this window
                
                if op.end_time <= search_start:
                    continue  # Before our search range
                
                # Try after this operation
                gap_start = max(search_start, op.end_time)
                if gap_start + duration <= window_end:
                    if self.is_available(gap_start, gap_start + duration):
                        return gap_start
        
        return None  # No available slot found
    
    def get_utilization(self, start: float, end: float) -> float:
        """
        Calculate resource utilization (% busy time) in a given time range.
        
        Args:
            start: Start of time range (Unix timestamp)
            end: End of time range (Unix timestamp)
            
        Returns:
            float: Utilization as a fraction between 0.0 and 1.0 (0% to 100%)
            
        Example:
            >>> # Check utilization during work day
            >>> util = resource.get_utilization(day_start.timestamp(), day_end.timestamp())
            >>> print(f"Resource is {util * 100:.1f}% utilized")
        """
        if end <= start:
            return 0.0
        
        total_time = end - start
        busy_time = 0.0
        
        for op in self.schedule:
            # Skip operations outside our time range
            if op.end_time <= start or op.start_time >= end:
                continue
            
            # Calculate overlap
            overlap_start = max(start, op.start_time)
            overlap_end = min(end, op.end_time)
            busy_time += overlap_end - overlap_start
        
        return busy_time / total_time
    
    def get_schedule_gaps(self, start: float = None, end: float = None) -> List[Tuple[float, float]]:
        """
        Find all gaps (idle periods) in the resource's schedule.
        
        Args:
            start: Start of time range to check (default: start of first operation)
            end: End of time range to check (default: end of last operation)
            
        Returns:
            List[Tuple[float, float]]: List of (gap_start, gap_end) tuples
            
        Example:
            >>> gaps = resource.get_schedule_gaps()
            >>> for gap_start, gap_end in gaps:
            ...     duration = gap_end - gap_start
            ...     print(f"Gap: {duration / 3600:.1f} hours")
        """
        if not self.schedule:
            return []
        
        gaps = []
        
        # Determine time range
        if start is None:
            start = self.schedule[0].start_time
        if end is None:
            end = self.schedule[-1].end_time
        
        # Check gap before first operation
        if self.schedule[0].start_time > start:
            gaps.append((start, self.schedule[0].start_time))
        
        # Check gaps between operations
        for i in range(len(self.schedule) - 1):
            gap_start = self.schedule[i].end_time
            gap_end = self.schedule[i + 1].start_time
            if gap_end > gap_start:
                gaps.append((gap_start, gap_end))
        
        # Check gap after last operation
        if self.schedule[-1].end_time < end:
            gaps.append((self.schedule[-1].end_time, end))
        
        return gaps
    
    def clear_schedule(self):
        """
        Remove all operations from this resource's schedule.
        
        This does NOT unschedule the operations themselves - they will still have
        their start_time, end_time, and resource_id set. Use Schedule.clear_all()
        for a complete reset.
        
        Example:
            >>> resource.clear_schedule()
            >>> assert len(resource.schedule) == 0
        """
        self.schedule.clear()
    
    def get_total_scheduled_time(self) -> float:
        """
        Get the total duration of all scheduled operations.
        
        Returns:
            float: Sum of all operation durations in seconds
            
        Example:
            >>> total = resource.get_total_scheduled_time()
            >>> print(f"Resource has {total / 3600:.1f} hours scheduled")
        """
        return sum(op.duration for op in self.schedule)
    
    def __repr__(self):
        """
        Return a detailed string representation of the resource.
        
        Returns:
            str: String representation with key attributes
        """
        return (f"Resource(id={self.resource_id}, type={self.resource_type}, "
                f"name={self.resource_name}, scheduled_ops={len(self.schedule)})")