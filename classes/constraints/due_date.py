"""
Due date constraint.
"""

from typing import Optional

from .constraint import Constraint


class DueDateConstraint(Constraint):
    """
    Enforces due dates from job metadata or an explicit map.
    """

    def __init__(self, due_dates: Optional[dict] = None, strict: bool = True):
        self.due_dates = due_dates or {}
        self.strict = strict

    def _get_due_date(self, schedule, operation) -> Optional[float]:
        if operation.job_id in self.due_dates:
            return self.due_dates[operation.job_id]
        job = schedule.jobs.get(operation.job_id)
        if not job:
            return None
        due = job.metadata.get("due_date")
        if due is None:
            return None
        return due.timestamp()

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        due_ts = self._get_due_date(schedule, operation)
        if due_ts is None:
            return True
        if not self.strict:
            return True
        return end_ts <= due_ts

    def adjust_earliest_start(self, schedule, operation, resource, earliest_start: float) -> float:
        return earliest_start
