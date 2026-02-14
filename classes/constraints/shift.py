"""
Shift constraint.
"""

from datetime import datetime, time, timedelta
from typing import Optional

from .constraint import Constraint


class ShiftConstraint(Constraint):
    """
    Enforces recurring daily shift windows.

    Modes:
      - "strict": operation must fit entirely within a shift window
      - "allow_overrun": operation must start within a shift window
      - "ignore": no shift enforcement
    """

    def __init__(
        self,
        shift_start: Optional[time] = None,
        shift_end: Optional[time] = None,
        mode: str = "strict",
        resource_type_filter: Optional[list] = None,
        shift_windows: Optional[list] = None,
    ):
        if mode not in {"strict", "allow_overrun", "ignore"}:
            raise ValueError("mode must be one of: strict, allow_overrun, ignore")
        if shift_windows is None:
            if shift_start is None or shift_end is None:
                raise ValueError("Provide shift_start/shift_end or shift_windows")
            shift_windows = [(shift_start, shift_end)]
        self.shift_windows = shift_windows
        self.mode = mode
        self.resource_type_filter = resource_type_filter

    def _get_shift_windows_for_day(self, dt: datetime) -> list:
        """
        Return all shift windows for the day containing dt.
        Handles overnight shifts (end <= start), including windows that
        started on the previous day and carry into this day.
        """
        day = dt.date()
        windows = []
        for start_t, end_t in self.shift_windows:
            start_dt = datetime.combine(day, start_t)
            end_dt = datetime.combine(day, end_t)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            windows.append((start_dt, end_dt))

            # Also include previous-day anchor for overnight windows so times
            # after midnight are recognized as being within the active shift.
            if end_t <= start_t:
                prev_start_dt = start_dt - timedelta(days=1)
                prev_end_dt = end_dt - timedelta(days=1)
                windows.append((prev_start_dt, prev_end_dt))
        return windows

    def _is_in_shift(self, dt: datetime) -> bool:
        return any(start <= dt < end for start, end in self._get_shift_windows_for_day(dt))

    def _next_shift_start(self, dt: datetime) -> datetime:
        windows = self._get_shift_windows_for_day(dt)
        for start_dt, _ in sorted(windows):
            if dt < start_dt:
                return start_dt
        # Next day, earliest shift start
        next_day = dt + timedelta(days=1)
        next_windows = self._get_shift_windows_for_day(next_day)
        return min(start for start, _ in next_windows)

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        if self.mode == "ignore":
            return True
        if self.resource_type_filter and resource.resource_type not in self.resource_type_filter:
            return True

        start_dt = datetime.fromtimestamp(start_ts)
        end_dt = datetime.fromtimestamp(end_ts)

        if self.mode == "allow_overrun":
            return self._is_in_shift(start_dt)

        # strict mode: must fit within any single window
        for shift_start, shift_end in self._get_shift_windows_for_day(start_dt):
            if shift_start <= start_dt and end_dt <= shift_end:
                return True
        return False

    def adjust_earliest_start(self, schedule, operation, resource, earliest_start: float) -> float:
        if self.mode == "ignore":
            return earliest_start
        if self.resource_type_filter and resource.resource_type not in self.resource_type_filter:
            return earliest_start

        dt = datetime.fromtimestamp(earliest_start)
        if self._is_in_shift(dt):
            return earliest_start
        return self._next_shift_start(dt).timestamp()
