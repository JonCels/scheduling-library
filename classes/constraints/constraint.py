"""
Constraint base class for scheduling rules.
"""


class Constraint:
    """
    Base class for scheduling constraints.

    Override is_feasible to enforce hard constraints. Optionally override
    adjust_earliest_start to push a proposed start time forward.
    """

    def is_feasible(self, schedule, operation, resource, start_ts: float, end_ts: float) -> bool:
        return True

    def adjust_earliest_start(
        self, schedule, operation, resource, earliest_start: float
    ) -> float:
        return earliest_start

    def __repr__(self) -> str:
        return self.__class__.__name__
