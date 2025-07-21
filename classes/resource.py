from sortedcontainers import SortedList
from typing import Optional, List, Tuple
from operation import Operation

class Resource:
    def __init__(
        self,
        resource_id: str,
        resource_type: str,
        resource_name: str,
        availability_windows: Optional[List[Tuple[float, float]]] = None,
    ):
        self.resource_id = resource_id  
        self.resource_type = resource_type
        self.resource_name = resource_name
        self.availability_windows = availability_windows or []
        self.schedule = SortedList() # SortedList of Operations sorted by start_time

    def is_available(self, start: float, end: float) -> bool:
        if self.availability_windows:
            # Entire [start,end) lies within some availability window
            if not any(ws <= start and end <= we for ws, we in self.availability_windows):
                return False

        # Reject if no scheduled operations
        if not self.schedule:
            return True

        # Use binary search to find possible overlapping operations
        # Find position where this operation would be inserted
        dummy_op = Operation("dummy", "dummy", 0, self.resource_type, start_time=start, end_time=end)
        pos = self.schedule.bisect_left(dummy_op)

        # Check operation before pos
        if pos > 0:
            prev_op = self.schedule[pos - 1]
            if prev_op.end_time > start:
                return False

        # Check operation at pos
        if pos < len(self.schedule):
            next_op = self.schedule[pos]
            if next_op.start_time < end:
                return False

        return True

    def add_operation(self, operation: Operation) -> bool:
        if not operation.start_time or not operation.end_time:
            raise ValueError("Operation must have start_time and end_time before scheduling")

        if operation.resource_type != self.resource_type:
            raise ValueError(f"Operation with resource type {operation.resource_type} can't be scheduled on resource {self.resource_name} with type {self.resource_type}")

        if not self.is_available(operation.start_time, operation.end_time):
            return False

        self.schedule.add(operation)
        return True

    def remove_operation(self, operation: Operation):
        self.schedule.discard(operation)