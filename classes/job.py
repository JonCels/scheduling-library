"""
Job class for the scheduling library.

A Job represents a unit of work that needs to be completed, composed of one or more
operations that must be scheduled on resources.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from operation import Operation


class Job:
    """
    Represents a unit of work in the scheduling system.
    
    A Job is composed of one or more operations that need to be completed. Jobs can
    have metadata attached (e.g., customer information, priority, due dates) to help
    with scheduling decisions.
    
    Attributes:
        job_id (str): Unique identifier for the job
        operations (List[Operation]): List of operations that make up this job
        metadata (dict): Optional dictionary for storing additional job information
                        (e.g., {'customer': 'ABC Corp', 'priority': 'high', 'due_date': datetime})
    
    Example:
        >>> operations = [Operation(...), Operation(...)]
        >>> job = Job("JOB_001", operations, {"customer": "ABC Corp", "priority": "high"})
    """
    
    def __init__(self, job_id: str, operations: List["Operation"], metadata: Optional[dict] = None):
        """
        Initialize a new Job.
        
        Args:
            job_id: Unique identifier for this job
            operations: List of operations that comprise this job
            metadata: Optional dictionary for additional job information
        """
        self.job_id = job_id
        self.operations = operations
        self.metadata = metadata or {}