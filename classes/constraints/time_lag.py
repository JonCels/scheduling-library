"""
Time lag constraint.
"""

from typing import Optional

from .constraint import Constraint


class TimeLagConstraint(Constraint):
    """
    Enforces min/max waiting time after predecessors complete.

    Looks for operation.metadata keys:
      - min_delay_seconds: float
      - max_delay_seconds: float
    """

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
        min_delay = operation.metadata.get("min_delay_seconds")
        if min_delay is None:
            return earliest_start
        pred_end = self._get_pred_end(schedule, operation)
        if pred_end is None:
            return earliest_start
        return max(earliest_start, pred_end + float(min_delay))

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        max_delay = operation.metadata.get("max_delay_seconds")
        if max_delay is None:
            return True
        pred_end = self._get_pred_end(schedule, operation)
        if pred_end is None:
            return True
        return start_ts <= pred_end + float(max_delay)
