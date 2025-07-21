from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from operation import Operation

class Job:
    def __init__(self, job_id: str, operations: List["Operation"], metadata: Optional[dict] = None):
        self.job_id = job_id
        self.operations = operations
        self.metadata = metadata or {}