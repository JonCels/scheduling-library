import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'classes'))

# Import the example creation function
from example_usage import create_example_schedule, schedule_operations

def main():
    # Create and populate the schedule
    schedule = create_example_schedule()
    schedule_operations(schedule)
    
    # Generate Mermaid Gantt chart
    mermaid_chart = schedule.create_mermaid_gantt()
    print("Mermaid Gantt Chart:")
    print("=" * 50)
    print(mermaid_chart)

if __name__ == "__main__":
    main() 