"""
Job class for the scheduling library.

A Job represents a unit of work that needs to be completed, composed of one or more
operations that must be scheduled on resources.
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from classes.operation import Operation


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
    
    def is_complete(self) -> bool:
        """
        Check if all operations in this job are scheduled.
        
        Returns:
            bool: True if all operations have been scheduled, False otherwise
            
        Example:
            >>> if job.is_complete():
            ...     print(f"Job {job.job_id} is fully scheduled")
        """
        return all(op.is_scheduled() for op in self.operations)
    
    def get_scheduled_operations(self) -> List["Operation"]:
        """
        Get list of operations that have been scheduled.
        
        Returns:
            List[Operation]: Operations with start_time and end_time assigned
            
        Example:
            >>> scheduled = job.get_scheduled_operations()
            >>> print(f"{len(scheduled)} operations scheduled")
        """
        return [op for op in self.operations if op.is_scheduled()]
    
    def get_unscheduled_operations(self) -> List["Operation"]:
        """
        Get list of operations that have not been scheduled yet.
        
        Returns:
            List[Operation]: Operations without scheduling information
            
        Example:
            >>> unscheduled = job.get_unscheduled_operations()
            >>> for op in unscheduled:
            ...     print(f"Still need to schedule: {op.operation_id}")
        """
        return [op for op in self.operations if not op.is_scheduled()]
    
    def get_start_time(self) -> Optional[float]:
        """
        Get the earliest start time of any operation in this job.
        
        Returns:
            float: Unix timestamp of earliest operation start, or None if no operations scheduled
            
        Example:
            >>> start = job.get_start_time()
            >>> if start:
            ...     print(f"Job starts at {datetime.fromtimestamp(start)}")
        """
        scheduled_ops = self.get_scheduled_operations()
        if not scheduled_ops:
            return None
        return min(op.start_time for op in scheduled_ops)
    
    def get_end_time(self) -> Optional[float]:
        """
        Get the latest end time of any operation in this job.
        
        Returns:
            float: Unix timestamp of latest operation end, or None if no operations scheduled
            
        Example:
            >>> end = job.get_end_time()
            >>> if end:
            ...     print(f"Job completes at {datetime.fromtimestamp(end)}")
        """
        scheduled_ops = self.get_scheduled_operations()
        if not scheduled_ops:
            return None
        return max(op.end_time for op in scheduled_ops)
    
    def get_makespan(self) -> Optional[float]:
        """
        Get the total time from first operation start to last operation end.
        
        This is the "wall clock" time the job takes, accounting for any gaps
        or parallel operations.
        
        Returns:
            float: Duration in seconds from start to finish, or None if not fully scheduled
            
        Example:
            >>> makespan = job.get_makespan()
            >>> if makespan:
            ...     print(f"Job takes {makespan / 3600:.1f} hours total")
        """
        start = self.get_start_time()
        end = self.get_end_time()
        if start is None or end is None:
            return None
        return end - start
    
    def get_total_duration(self) -> float:
        """
        Get the sum of all operation durations.
        
        This is the total processing time required, ignoring any parallelism.
        
        Returns:
            float: Sum of all operation durations in seconds
            
        Example:
            >>> total = job.get_total_duration()
            >>> print(f"Job requires {total / 3600:.1f} hours of processing")
        """
        return sum(op.duration for op in self.operations)
    
    def get_operations_by_resource_type(self, resource_type: str) -> List["Operation"]:
        """
        Get all operations that require a specific resource type.
        
        Args:
            resource_type: The resource type to filter by
            
        Returns:
            List[Operation]: Operations requiring this resource type
            
        Example:
            >>> machining_ops = job.get_operations_by_resource_type("machining")
        """
        return [op for op in self.operations if op.resource_type == resource_type]
    
    def __repr__(self):
        """
        Return a detailed string representation of the job.
        
        Returns:
            str: String representation with key attributes
        """
        status = "complete" if self.is_complete() else f"{len(self.get_scheduled_operations())}/{len(self.operations)} ops scheduled"
        return f"Job(id={self.job_id}, operations={len(self.operations)}, status={status})"