/* This example is meant to use the library to solve a simple scheduling problem.
Here are the details of the problem:
  - Resources:
    - Holding bay (6 slots)
    - Prep station
    - Enerpack drop station (bottleneck)
    - Add-on drop station
    - Parking bay (8 slots)
    - East Aisle
    - West Aisle

  - Jobs:
    - Module type A
    - Module type B
    - Module type C

  - Operations:
    - Module waiting in holding bay
    - Module type A in prep station (15 minutes)
    - Module type B in prep station (10 minutes)
    - Module type C in prep station (20 minutes)
    - Module type A in Enerpack drop station (2 hours)
    - Module type B in Enerpack drop station (2.5 hours)
    - Module type C in Enerpack drop station (3 hours)
    - Module type A in add-on drop station (30 minutes)
    - Module type B in add-on drop station (30 minutes)
    - Move module type A from holding bay to prep station (12 minutes)
        - Uses the East Aisle
    - Move module type A from prep station to Enerpack drop station (20 minutes)
        - Uses the East Aisle
    - Move module type A from Enerpack drop station to add-on drop station (6 minutes)
        - Uses the Enerpack drop station and add-on drop station
    - Move module type A from add-on drop station to parking bay (12 minutes)
        - Uses the West Aisle
    - Move module type B from holding bay to prep station (12 minutes)
        - Uses the East Aisle
    - Move module type B from prep station to Enerpack drop station (23 minutes)
        - Uses the East Aisle
    - Move module type B from Enerpack drop station to add-on drop station (6 minutes)
        - Uses the Enerpack drop station and add-on drop station
    - Move module type B from add-on drop station to parking bay (12 minutes)
        - Uses the West Aisle
    - Move module type C from holding bay to prep station (10 minutes)
        - Uses the East Aisle
    - Move module type C from prep station to Enerpack drop station (18 minutes)
        - Uses the East Aisle
    - Move module type C from Enerpack drop station to parking bay (15 minutes)
        - Uses the East Aisle
*/

from datetime import datetime, timedelta
from typing import List
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'classes'))

from classes.job import Job
from classes.operation import Operation
from classes.resource import Resource
from classes.schedule import Schedule

def main():
    print("FOK Example")
    print("=" * 50)
    
    start_date = datetime(2026, 2, 2, 8, 0)  # Monday 8 AM
    end_date = datetime(2026, 2, 2, 17, 0)   # Monday 5 PM

    schedule = Schedule(
        name="FOK Schedule - 2026-02-02",
        schedule_id="FOK_SCHED_260202",
        start_date=start_date,
        end_date=end_date
    )

    resources = [
        Resource("HOLDING_BAY", "holding", "Holding Bay"),
        Resource("PREP_STATION", "processing", "Prep Station"),
        Resource("ENERPACK_DROP_STATION", "processing", "Enerpack Drop Station"),
        Resource("ADD_ON_DROP_STATION", "processing", "Add-on Drop Station"),
        Resource("EAST_AISLE", "transport", "East Aisle"),
        Resource("WEST_AISLE", "transport", "West Aisle"),
        Resource("PARKING_BAY_1", "holding", "Parking Bay 1"),
        Resource("PARKING_BAY_2", "holding", "Parking Bay 2"),
        Resource("PARKING_BAY_3", "holding", "Parking Bay 3"),
        Resource("PARKING_BAY_4", "holding", "Parking Bay 4"),
        Resource("PARKING_BAY_5", "holding", "Parking Bay 5"),
        Resource("PARKING_BAY_6", "holding", "Parking Bay 6"),
        Resource("PARKING_BAY_7", "holding", "Parking Bay 7"),
        Resource("PARKING_BAY_8", "holding", "Parking Bay 8"),
    ];

    operations = [
        Operation("MODULE_WAITING_IN_HOLDING_BAY", "MODULE_A", 0, "holding", ["HOLDING_BAY"], [], {"module_type": "A"}),
        Operation("MODULE_TYPE_A_IN_PREP_STATION", "MODULE_A", 15, "processing", ["PREP_STATION"], ["MODULE_WAITING_IN_HOLDING_BAY"], {"module_type": "A"}),
        Operation("MODULE_TYPE_B_IN_PREP_STATION", "MODULE_B", 10, "processing", ["PREP_STATION"], ["MODULE_WAITING_IN_HOLDING_BAY"], {"module_type": "B"}),
        Operation("MODULE_TYPE_C_IN_PREP_STATION", "MODULE_C", 20, "processing", ["PREP_STATION"], ["MODULE_WAITING_IN_HOLDING_BAY"], {"module_type": "C"}),
        Operation("MODULE_TYPE_A_IN_ENERPACK_DROP_STATION", "MODULE_A", 120, "processing", ["ENERPACK_DROP_STATION"], ["MODULE_TYPE_A_IN_PREP_STATION"], {"module_type": "A"}),
        Operation("MODULE_TYPE_B_IN_ENERPACK_DROP_STATION", "MODULE_B", 150, "processing", ["ENERPACK_DROP_STATION"], ["MODULE_TYPE_B_IN_PREP_STATION"], {"module_type": "B"}),
        Operation("MODULE_TYPE_C_IN_ENERPACK_DROP_STATION", "MODULE_C", 180, "processing", ["ENERPACK_DROP_STATION"], ["MODULE_TYPE_C_IN_PREP_STATION"], {"module_type": "C"}),
    ];
    
if __name__ == "__main__":
    main() 