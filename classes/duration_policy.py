"""
Duration adjustment policies for schedule-time duration modifiers.
"""

from typing import Callable


class DurationAdjustmentPolicy:
    """
    Base policy for dynamic duration adjustments.

    Implementations return additional seconds to add on top of operation.duration
    for a specific resource assignment.
    """

    def get_adjustment_seconds(self, schedule, operation, assigned_resources: dict) -> float:
        return 0.0


class CallableDurationAdjustmentPolicy(DurationAdjustmentPolicy):
    """
    Adapter policy that delegates to a user-supplied callable.
    """

    def __init__(self, adjustment_fn: Callable):
        self._adjustment_fn = adjustment_fn

    def get_adjustment_seconds(self, schedule, operation, assigned_resources: dict) -> float:
        value = self._adjustment_fn(schedule, operation, assigned_resources)
        return float(value) if value is not None else 0.0
