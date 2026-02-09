"""
Changeover constraint.
"""

from typing import Optional, List

from .constraint import Constraint


class ChangeoverConstraint(Constraint):
    """
    Adds changeover time when switching keys on a resource.

    Defaults to job metadata "job_type" for backwards compatibility.
    """

    def __init__(
        self,
        changeover_minutes: float,
        key_from: str = "job_meta",
        key_field: str = "job_type",
        resource_type_filter: Optional[List[str]] = None,
    ):
        self.changeover_seconds = changeover_minutes * 60
        self.key_from = key_from
        self.key_field = key_field
        self.resource_type_filter = resource_type_filter

    def _get_key(self, schedule, operation) -> Optional[str]:
        if self.key_from == "job_meta":
            job = schedule.jobs.get(operation.job_id)
            if not job:
                return None
            return job.metadata.get(self.key_field)
        if self.key_from == "operation_meta":
            return operation.metadata.get(self.key_field)
        if self.key_from == "assigned_resource":
            value = operation.assigned_resources.get(self.key_field)
            if isinstance(value, list):
                return value[0] if value else None
            return value
        return None

    def _requires_changeover(self, schedule, prev_op, next_op) -> bool:
        if self.changeover_seconds <= 0 or not prev_op or not next_op:
            return False
        prev_key = self._get_key(schedule, prev_op)
        next_key = self._get_key(schedule, next_op)
        if not prev_key or not next_key:
            return False
        return prev_key != next_key

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        if self.changeover_seconds <= 0 or not resource.schedule:
            return True
        if self.resource_type_filter and resource.resource_type not in self.resource_type_filter:
            return True

        prev_op = None
        next_op = None
        for scheduled_op in resource.schedule:
            if scheduled_op.start_time < start_ts:
                prev_op = scheduled_op
                continue
            next_op = scheduled_op
            break

        if prev_op and self._requires_changeover(schedule, prev_op, operation):
            if start_ts < prev_op.end_time + self.changeover_seconds:
                return False

        if next_op and self._requires_changeover(schedule, operation, next_op):
            if end_ts + self.changeover_seconds > next_op.start_time:
                return False

        return True

    def adjust_earliest_start(self, schedule, operation, resource, earliest_start: float) -> float:
        if self.changeover_seconds <= 0 or not resource.schedule:
            return earliest_start
        if self.resource_type_filter and resource.resource_type not in self.resource_type_filter:
            return earliest_start

        prev_op = None
        for scheduled_op in resource.schedule:
            if scheduled_op.start_time < earliest_start:
                prev_op = scheduled_op
                continue
            break

        if prev_op and self._requires_changeover(schedule, prev_op, operation):
            return max(earliest_start, prev_op.end_time + self.changeover_seconds)

        return earliest_start
