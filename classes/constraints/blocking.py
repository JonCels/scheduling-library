"""
Blocking (no-wait) constraint.
"""

from typing import Optional

from .constraint import Constraint


class BlockingConstraint(Constraint):
    """
    Enforces a no-wait rule between precedence-related operations in a job.
    """

    def __init__(self, epsilon_seconds: float = 1e-6):
        self.epsilon_seconds = epsilon_seconds

    def _get_pred_end(self, schedule, operation) -> Optional[float]:
        if not operation.precedence:
            return None
        pred_ops = []
        for pred_id in operation.precedence:
            pred_op = schedule.operations.get(pred_id)
            if pred_op and pred_op.end_time is not None:
                pred_ops.append(pred_op.end_time)
        if not pred_ops:
            return None
        return max(pred_ops)

    def adjust_earliest_start(self, schedule, operation, resource, earliest_start: float) -> float:
        pred_end = self._get_pred_end(schedule, operation)
        if pred_end is None:
            return earliest_start
        return max(earliest_start, pred_end)

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        pred_end = self._get_pred_end(schedule, operation)
        if pred_end is None:
            return True
        return abs(start_ts - pred_end) <= self.epsilon_seconds
