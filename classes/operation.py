from typing import List, Optional

class Operation:
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
        self.operation_id = operation_id
        self.job_id = job_id
        self.duration = duration
        self.resource_type = resource_type  # e.g. "tank", "line", etc.
        self.possible_resource_ids = possible_resource_ids or []
        self.precedence = precedence or []
        self.metadata = metadata or {}
        self.start_time = start_time
        self.end_time = end_time
        self.resource_id = resource_id

    def is_scheduled(self) -> bool:
        return self.start_time is not None and self.end_time is not None

    def __lt__(self, other):
        # For sorting by start_time, unscheduled operations come last
        if self.start_time is None:
            return False

        if other.start_time is None:
            return True

        return self.start_time < other.start_time