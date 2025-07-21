from datetime import datetime, timedelta
from typing import Dict

# Optional matplotlib imports for visual charts
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib.patches import Rectangle
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class Schedule:
    def __init__(
        self, 
        name: str, 
        schedule_id: str, 
        start_date: datetime, 
        end_date: datetime
    ):
        self.name = name
        self.schedule_id = schedule_id
        self.start_date = start_date
        self.end_date = end_date
        self.jobs: Dict[str, "Job"] = {}
        self.resources: Dict[str, "Resource"] = {}
        self.operations: Dict[str, "Operation"] = {}

    def __str__(self):
        return f"{self.name} - {self.schedule_id} - {self.start_date} - {self.end_date}"

    def add_job(self, job: "Job"):
        self.jobs[job.job_id] = job
        for op in job.operations:
            self.operations[op.operation_id] = op

    def add_resource(self, resource: "Resource"):
        self.resources[resource.resource_id] = resource

    def schedule_operation(self, operation_id: str, resource_id: str, start_time: datetime) -> bool:
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")

        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")

        op = self.operations[operation_id]
        resource = self.resources[resource_id]

        # Resource type compatibility
        if resource.resource_type != op.resource_type:
            raise ValueError(f"Resource with type {resource.resource_type} is not allowed for operation with type {op.resource_type}")

        # Resource id compatibility
        if resource_id not in op.possible_resource_ids:
            raise ValueError(f"Resource {resource_id} is not allowed for operation {operation_id}")

        # Convert datetime to timestamp for calculations
        start_timestamp = start_time.timestamp()
        end_timestamp = start_timestamp + op.duration

        # Resource available
        if not resource.is_available(start_timestamp, end_timestamp):
            return False
        
        # Precedence check
        for pred_op_id in op.precedence:
            pred_op = self.operations.get(pred_op_id)
            if not pred_op or pred_op.end_time is None or pred_op.end_time > start_timestamp:
                return False  # Can't schedule yet
                
        # Assign scheduling info
        op.resource_id = resource_id
        op.start_time = start_timestamp
        op.end_time = end_timestamp

        # Add operation to resource schedule
        success = resource.add_operation(op)
        if not success:
            # Rollback if failed
            op.resource_id = None
            op.start_time = None
            op.end_time = None
            return False

        return True

    def unschedule_operation(self, operation_id: str):
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")
            
        op = self.operations[operation_id]
        if not op.is_scheduled():
            return

        resource = self.resources.get(op.resource_id)
        if resource:
            resource.remove_operation(op)

        # Reset scheduling info
        op.resource_id = None
        op.start_time = None
        op.end_time = None

    def create_gantt_chart(self):
        """
        Create a Gantt chart representation of the schedule
        """
        print(f"\n=== Gantt Chart ===")
        print(f"Schedule: {self.name}")
        
        # Collect all operations and sort by start time
        all_operations = []
        for resource in self.resources.values():
            for operation in resource.schedule:
                all_operations.append(operation)
        
        if not all_operations:
            print("No operations scheduled")
            return
            
        all_operations.sort(key=lambda op: op.start_time)
        
        # Find the time range
        earliest_start = min(op.start_time for op in all_operations)
        latest_end = max(op.end_time for op in all_operations)
        
        earliest_dt = datetime.fromtimestamp(earliest_start)
        latest_dt = datetime.fromtimestamp(latest_end)
        
        print(f"Time Range: {earliest_dt.strftime('%a %H:%M')} - {latest_dt.strftime('%a %H:%M')}")
        print()
        
        # Group operations by job
        jobs_operations = {}
        for operation in all_operations:
            job_id = operation.job_id
            if job_id not in jobs_operations:
                jobs_operations[job_id] = []
            jobs_operations[job_id].append(operation)
        
        # Print Gantt chart for each job
        for job_id in sorted(jobs_operations.keys()):
            job = self.jobs.get(job_id)
            customer = job.metadata.get('customer', 'Unknown') if job else 'Unknown'
            priority = job.metadata.get('priority', 'Unknown') if job else 'Unknown'
            
            print(f"{job_id} ({customer} - {priority} priority):")
            
            operations = jobs_operations[job_id]
            operations.sort(key=lambda op: op.start_time)
            
            for operation in operations:
                start_dt = datetime.fromtimestamp(operation.start_time)
                end_dt = datetime.fromtimestamp(operation.end_time)
                duration_hours = (operation.end_time - operation.start_time) / 3600
                
                # Create visual bar
                bar_length = max(1, int(duration_hours * 4))  # 4 chars per hour
                bar = "█" * bar_length
                
                print(f"  {operation.operation_id:>8}: {start_dt.strftime('%a %H:%M')} |{bar}| {end_dt.strftime('%H:%M')} [{operation.resource_id}] ({duration_hours:.1f}h)")
            
            print()

    def show_visual_gantt_chart(self):
        """
        Create and display a visual Gantt chart using matplotlib
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Error: matplotlib is required for visual Gantt charts. Install with: pip install matplotlib")
            return
        
        # Collect all operations and sort by start time
        all_operations = []
        for resource in self.resources.values():
            for operation in resource.schedule:
                all_operations.append(operation)
        
        if not all_operations:
            print("No operations scheduled to display")
            return
        
        # Group operations by job for color coding
        jobs_operations = {}
        for operation in all_operations:
            job_id = operation.job_id
            if job_id not in jobs_operations:
                jobs_operations[job_id] = []
            jobs_operations[job_id].append(operation)
        
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Define colors for different jobs
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3', '#54A0FF']
        job_colors = {}
        for i, job_id in enumerate(sorted(jobs_operations.keys())):
            job_colors[job_id] = colors[i % len(colors)]
        
        # Get all resources for y-axis
        resources = list(self.resources.keys())
        resources.sort()
        
        # Create y-position mapping
        y_positions = {resource: i for i, resource in enumerate(resources)}
        
        # Plot operations
        for operation in all_operations:
            start_dt = datetime.fromtimestamp(operation.start_time)
            end_dt = datetime.fromtimestamp(operation.end_time)
            duration = end_dt - start_dt
            
            y_pos = y_positions[operation.resource_id]
            color = job_colors[operation.job_id]
            
            # Create rectangle for the operation
            # Convert duration to matplotlib date units (days)
            duration_days = duration.total_seconds() / (24 * 3600)
            rect = Rectangle(
                (mdates.date2num(start_dt), y_pos - 0.4),
                duration_days,
                0.8,
                facecolor=color,
                edgecolor='black',
                alpha=0.7
            )
            ax.add_patch(rect)
            
            # Add operation label
            mid_time = start_dt + duration / 2
            ax.text(
                mdates.date2num(mid_time),
                y_pos,
                operation.operation_id,
                ha='center',
                va='center',
                fontsize=8,
                fontweight='bold',
                color='white' if sum(int(color[i:i+2], 16) for i in (1, 3, 5)) < 300 else 'black'
            )
        
        # Set up the plot
        ax.set_ylim(-0.5, len(resources) - 0.5)
        ax.set_yticks(range(len(resources)))
        ax.set_yticklabels([f"{res}\n({self.resources[res].resource_name})" for res in resources])
        
        # Format x-axis for time
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        ax.xaxis.set_minor_locator(mdates.MinuteLocator(interval=30))
        
        # Set time range
        if all_operations:
            earliest_start = min(op.start_time for op in all_operations)
            latest_end = max(op.end_time for op in all_operations)
            start_dt = datetime.fromtimestamp(earliest_start)
            end_dt = datetime.fromtimestamp(latest_end)
            
            # Add some padding
            padding = timedelta(minutes=30)
            ax.set_xlim(
                mdates.date2num(start_dt - padding),
                mdates.date2num(end_dt + padding)
            )
        
        # Customize the plot
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Resources', fontsize=12)
        ax.set_title(f'{self.name}\nGantt Chart - {self.start_date.strftime("%Y-%m-%d")}', fontsize=14, fontweight='bold')
        
        # Rotate x-axis labels for better readability
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Create legend
        legend_elements = []
        for job_id in sorted(jobs_operations.keys()):
            job = self.jobs.get(job_id)
            customer = job.metadata.get('customer', 'Unknown') if job else 'Unknown'
            priority = job.metadata.get('priority', 'Unknown') if job else 'Unknown'
            
            legend_elements.append(
                Rectangle((0, 0), 1, 1, facecolor=job_colors[job_id], alpha=0.7,
                         label=f'{job_id} ({customer})')
            )
        
        ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.15, 1))
        
        # Adjust layout to prevent clipping
        plt.tight_layout()
        
        # Show the plot
        plt.show()
        
        return fig, ax