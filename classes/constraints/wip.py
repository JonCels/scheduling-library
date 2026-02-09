"""
WIP (work-in-process) limit constraint.
"""

from typing import List, Tuple

from .constraint import Constraint


class WipLimitConstraint(Constraint):
    """
    Enforces a max number of in-process jobs across resources.
    """

    def __init__(self, max_wip: int):
        if max_wip <= 0:
            raise ValueError("max_wip must be >= 1")
        self.max_wip = max_wip

    def _build_intervals(self, resource) -> List[Tuple[float, float, str]]:
        intervals = []
        for op in resource.schedule:
            intervals.append((op.start_time, op.end_time, op.job_id))
        return intervals

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        if start_ts >= end_ts:
            return False

        # Build intervals across all resources, including the proposed operation
        intervals = []
        for res in schedule.resources.values():
            intervals.extend(self._build_intervals(res))
        intervals.append((start_ts, end_ts, operation.job_id))

        # Sweep line on interval boundaries to check max concurrent jobs (unique job_id)
        events = []
        for s, e, job_id in intervals:
            events.append((s, 1, job_id))
            events.append((e, -1, job_id))
        events.sort()

        active_jobs = set()
        for _, delta, job_id in events:
            if delta == 1:
                active_jobs.add(job_id)
            else:
                active_jobs.discard(job_id)
            if len(active_jobs) > self.max_wip:
                return False

        return True
