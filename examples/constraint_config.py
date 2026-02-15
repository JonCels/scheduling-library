"""
Centralized configuration for vehicle testing schedule constraints.
"""

SCHEDULE_CONFIG = {
    "name": "Vehicle Emissions Testing - Day 1",
    "schedule_id": "VEH_TEST_DAY_1",
    "start_date": {"year": 2026, "month": 3, "day": 3, "hour": 0, "minute": 0},
    "end_date": {"year": 2026, "month": 3, "day": 4, "hour": 0, "minute": 0},
}

CONSTRAINT_CONFIG = {
    # Shift windows as ((start_hour, start_min), (end_hour, end_min)).
    # Use 00:00 to represent midnight/end-of-day boundaries.
    "shift_windows": {
        "midnight": ((0, 0), (6, 0)),
        "day": ((6, 0), (15, 30)),
        "afternoon": ((15, 30), (0, 0)),
    },
    "shift_mode": "strict",
    "shift_resource_type_filter": ["site", "vehicle"],
    "site_changeover_minutes": 30,
    "vehicle_transfer_minutes": 30,
    "enable_soak_constraint": True,
}

# Generic duration-adjustment configuration (independent of specific domain terms).
DURATION_ADJUSTMENT_CONFIG = {
    "base_additional_minutes": 20,  # applies to all assignments
    "resource_based_rules": {
        "resource_type": "site",
        "rules": [
            # Site numbers >= 6 get extra duration.
            {"id_number_min": 6, "additional_minutes": 10},
        ],
    },
}
