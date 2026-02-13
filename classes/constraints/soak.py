"""
Soak constraint.
"""

from typing import Optional

from .constraint import Constraint


class SoakConstraint(Constraint):
    """
    Enforces a per-operation soak lag on the same vehicle/job stream.

    This is metadata-driven and only applies to operations that define one of:
      - soak_seconds
      - soak_minutes
      - soak_hours

    Semantics:
    If an operation has a soak value, then its start must be at least
    (end time of the most recently finished scheduled operation in the same job)
    + soak lag.
    """

    def _get_soak_seconds(self, operation) -> Optional[float]:
        if "soak_seconds" in operation.metadata:
            return float(operation.metadata["soak_seconds"])
        if "soak_minutes" in operation.metadata:
            return float(operation.metadata["soak_minutes"]) * 60.0
        if "soak_hours" in operation.metadata:
            return float(operation.metadata["soak_hours"]) * 3600.0
        return None

    def _latest_prior_job_end(self, schedule, operation, start_ts: float) -> Optional[float]:
        latest_end = None
        for other in schedule.operations.values():
            if other.operation_id == operation.operation_id:
                continue
            if other.job_id != operation.job_id:
                continue
            if not other.is_scheduled() or other.end_time is None:
                continue
            # "last test on its vehicle" means completed tests before this start.
            if other.end_time <= start_ts and (latest_end is None or other.end_time > latest_end):
                latest_end = other.end_time
        return latest_end

    def adjust_earliest_start(self, schedule, operation, resource, earliest_start: float) -> float:
        soak_seconds = self._get_soak_seconds(operation)
        if soak_seconds is None or soak_seconds <= 0:
            return earliest_start
        prior_end = self._latest_prior_job_end(schedule, operation, earliest_start)
        if prior_end is None:
            return earliest_start
        return max(earliest_start, prior_end + soak_seconds)

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        soak_seconds = self._get_soak_seconds(operation)
        if soak_seconds is None or soak_seconds <= 0:
            return True
        prior_end = self._latest_prior_job_end(schedule, operation, start_ts)
        if prior_end is None:
            return True
        return start_ts >= prior_end + soak_seconds
