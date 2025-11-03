"""
Schedule class for the scheduling library.

The Schedule is the central orchestrator that manages jobs, operations, and resources,
and provides methods for scheduling operations and visualizing the results.
"""

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
    """
    Central class for managing jobs, operations, and resources in a scheduling system.
    
    The Schedule maintains the complete state of a scheduling problem, including all jobs,
    operations, and resources. It provides methods to:
    - Add jobs and resources
    - Schedule operations on resources
    - Validate scheduling constraints (precedence, resource availability, etc.)
    - Visualize schedules with Gantt charts
    
    Attributes:
        name (str): Human-readable name for the schedule
        schedule_id (str): Unique identifier for the schedule
        start_date (datetime): Start date/time of the scheduling period
        end_date (datetime): End date/time of the scheduling period
        jobs (Dict[str, Job]): Dictionary of jobs indexed by job_id
        resources (Dict[str, Resource]): Dictionary of resources indexed by resource_id
        operations (Dict[str, Operation]): Dictionary of all operations indexed by operation_id
    
    Example:
        >>> schedule = Schedule(
        ...     name="Production Schedule - Week 1",
        ...     schedule_id="SCHED_001",
        ...     start_date=datetime(2024, 1, 1, 8, 0),
        ...     end_date=datetime(2024, 1, 5, 17, 0)
        ... )
        >>> schedule.add_resource(machine)
        >>> schedule.add_job(job)
        >>> schedule.schedule_operation("OP_001", "MACHINE_001", datetime(2024, 1, 1, 8, 0))
    """
    
    def __init__(
        self, 
        name: str, 
        schedule_id: str, 
        start_date: datetime, 
        end_date: datetime
    ):
        """
        Initialize a new Schedule.
        
        Args:
            name: Human-readable name for the schedule
            schedule_id: Unique identifier
            start_date: Start of the scheduling period
            end_date: End of the scheduling period
        """
        self.name = name
        self.schedule_id = schedule_id
        self.start_date = start_date
        self.end_date = end_date
        self.jobs: Dict[str, "Job"] = {}
        self.resources: Dict[str, "Resource"] = {}
        self.operations: Dict[str, "Operation"] = {}

    def __str__(self):
        """Return a string representation of the schedule."""
        return f"{self.name} - {self.schedule_id} - {self.start_date} - {self.end_date}"

    def add_job(self, job: "Job"):
        """
        Add a job to the schedule.
        
        This also registers all of the job's operations in the schedule's operation
        dictionary for easy lookup.
        
        Args:
            job: The job to add
            
        Example:
            >>> job = Job("JOB_001", operations, {"customer": "ABC Corp"})
            >>> schedule.add_job(job)
        """
        self.jobs[job.job_id] = job
        for op in job.operations:
            self.operations[op.operation_id] = op

    def add_resource(self, resource: "Resource"):
        """
        Add a resource to the schedule.
        
        Resources must be added before operations can be scheduled on them.
        
        Args:
            resource: The resource to add
            
        Example:
            >>> resource = Resource("MACHINE_001", "machining", "CNC Machine 1")
            >>> schedule.add_resource(resource)
        """
        self.resources[resource.resource_id] = resource

    def schedule_operation(self, operation_id: str, resource_id: str, start_time: datetime) -> bool:
        """
        Schedule an operation on a specific resource at a specific time.
        
        This method performs comprehensive validation before scheduling:
        1. Operation and resource exist
        2. Resource type matches operation requirements
        3. Resource is in the operation's allowed resource list
        4. Resource is available during the time window
        5. All precedence constraints are satisfied
        
        If scheduling fails validation or availability checks, the operation remains
        unscheduled and the method returns False. If an error condition is detected
        (wrong types, missing entities), an exception is raised.
        
        Args:
            operation_id: ID of the operation to schedule
            resource_id: ID of the resource to schedule it on
            start_time: When the operation should start (datetime object)
            
        Returns:
            bool: True if scheduling succeeded, False if resource was not available
                  or precedence constraints were not met
                  
        Raises:
            KeyError: If operation_id or resource_id doesn't exist
            ValueError: If resource type doesn't match or resource not in allowed list
            
        Example:
            >>> start = datetime(2024, 1, 1, 8, 0)
            >>> success = schedule.schedule_operation("OP_001", "MACHINE_001", start)
            >>> if success:
            ...     print("Operation scheduled successfully")
        """
        # Validate operation exists
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")

        # Validate resource exists
        if resource_id not in self.resources:
            raise KeyError(f"Resource {resource_id} not found")

        op = self.operations[operation_id]
        resource = self.resources[resource_id]

        # Validate resource type compatibility
        if resource.resource_type != op.resource_type:
            raise ValueError(
                f"Resource with type {resource.resource_type} is not allowed "
                f"for operation with type {op.resource_type}"
            )

        # Validate resource is in the operation's allowed resource list
        if resource_id not in op.possible_resource_ids:
            raise ValueError(f"Resource {resource_id} is not allowed for operation {operation_id}")

        # Convert datetime to timestamp for internal calculations
        start_timestamp = start_time.timestamp()
        end_timestamp = start_timestamp + op.duration

        # Check resource availability
        if not resource.is_available(start_timestamp, end_timestamp):
            return False
        
        # Verify all precedence constraints are satisfied
        # All predecessor operations must be completed before this one can start
        for pred_op_id in op.precedence:
            pred_op = self.operations.get(pred_op_id)
            if not pred_op or pred_op.end_time is None or pred_op.end_time > start_timestamp:
                return False  # Predecessor not completed yet
                
        # All validations passed - assign scheduling information to the operation
        op.resource_id = resource_id
        op.start_time = start_timestamp
        op.end_time = end_timestamp

        # Add operation to the resource's schedule
        success = resource.add_operation(op)
        if not success:
            # Rollback if adding to resource failed
            op.resource_id = None
            op.start_time = None
            op.end_time = None
            return False

        return True

    def unschedule_operation(self, operation_id: str):
        """
        Remove an operation from its scheduled resource.
        
        This resets the operation to an unscheduled state, clearing its start_time,
        end_time, and resource_id. If the operation isn't currently scheduled, this
        method does nothing.
        
        Args:
            operation_id: ID of the operation to unschedule
            
        Raises:
            KeyError: If operation_id doesn't exist
            
        Example:
            >>> schedule.unschedule_operation("OP_001")
            >>> # Operation is now unscheduled and can be rescheduled
        """
        if operation_id not in self.operations:
            raise KeyError(f"Operation {operation_id} not found")
            
        op = self.operations[operation_id]
        
        # If already unscheduled, nothing to do
        if not op.is_scheduled():
            return

        # Remove from resource's schedule
        resource = self.resources.get(op.resource_id)
        if resource:
            resource.remove_operation(op)

        # Reset scheduling information
        op.resource_id = None
        op.start_time = None
        op.end_time = None

    def create_gantt_chart(self):
        """
        Create a text-based Gantt chart representation of the schedule.
        
        This method prints a console-friendly visualization of the schedule showing:
        - Time range of the schedule
        - Operations grouped by job
        - Visual bars representing operation duration
        - Resource assignments
        
        The chart is printed to stdout and suitable for quick visual inspection
        without requiring matplotlib.
        
        Example:
            >>> schedule.create_gantt_chart()
            === Gantt Chart ===
            Schedule: Production Schedule - Week 1
            Time Range: Mon 08:00 - Mon 13:30
            
            JOB_A (ABC Corp - high priority):
              A_MACH: Mon 08:00 |████████| 10:00 [MACHINE_001] (2.0h)
              A_ASSY: Mon 10:00 |████| 11:00 [ASSEMBLY_001] (1.0h)
        """
        print(f"\n=== Gantt Chart ===")
        print(f"Schedule: {self.name}")
        
        # Collect all scheduled operations from all resources
        all_operations = []
        for resource in self.resources.values():
            for operation in resource.schedule:
                all_operations.append(operation)
        
        if not all_operations:
            print("No operations scheduled")
            return
        
        # Sort chronologically for display
        all_operations.sort(key=lambda op: op.start_time)
        
        # Determine the time range covered by the schedule
        earliest_start = min(op.start_time for op in all_operations)
        latest_end = max(op.end_time for op in all_operations)
        
        earliest_dt = datetime.fromtimestamp(earliest_start)
        latest_dt = datetime.fromtimestamp(latest_end)
        
        print(f"Time Range: {earliest_dt.strftime('%a %H:%M')} - {latest_dt.strftime('%a %H:%M')}")
        print()
        
        # Organize operations by job for grouped display
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
                
                # Create visual bar (4 characters per hour of duration)
                bar_length = max(1, int(duration_hours * 4))
                bar = "█" * bar_length
                
                print(f"  {operation.operation_id:>8}: {start_dt.strftime('%a %H:%M')} |{bar}| {end_dt.strftime('%H:%M')} [{operation.resource_id}] ({duration_hours:.1f}h)")
            
            print()

    def show_visual_gantt_chart(self):
        """
        Create and display a visual Gantt chart using matplotlib.
        
        This method creates an interactive graphical Gantt chart with:
        - Color-coded operations by job
        - Resources on the y-axis
        - Time on the x-axis
        - Legend showing job details
        - Operation labels on bars
        
        The chart is displayed in a matplotlib window. This requires matplotlib
        to be installed. If matplotlib is not available, an error message is printed.
        
        Returns:
            tuple: (fig, ax) matplotlib figure and axis objects if successful,
                   None if matplotlib is not available or no operations are scheduled
                   
        Example:
            >>> schedule.show_visual_gantt_chart()
            # Opens a matplotlib window with an interactive Gantt chart
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
        
        # Plot operations as colored rectangles
        for operation in all_operations:
            start_dt = datetime.fromtimestamp(operation.start_time)
            end_dt = datetime.fromtimestamp(operation.end_time)
            duration = end_dt - start_dt
            
            y_pos = y_positions[operation.resource_id]
            color = job_colors[operation.job_id]
            
            # Create rectangle for the operation
            # Convert duration to matplotlib date units (days) for proper x-axis scaling
            duration_days = duration.total_seconds() / (24 * 3600)
            rect = Rectangle(
                (mdates.date2num(start_dt), y_pos - 0.4),  # Position and vertical centering
                duration_days,  # Width (duration)
                0.8,  # Height (leaves space between resources)
                facecolor=color,
                edgecolor='black',
                alpha=0.7
            )
            ax.add_patch(rect)
            
            # Add operation label in the center of the rectangle
            mid_time = start_dt + duration / 2
            # Choose text color based on background brightness (sum of RGB values)
            # Dark backgrounds get white text, light backgrounds get black text
            rgb_sum = sum(int(color[i:i+2], 16) for i in (1, 3, 5))
            text_color = 'white' if rgb_sum < 300 else 'black'
            ax.text(
                mdates.date2num(mid_time),
                y_pos,
                operation.operation_id,
                ha='center',
                va='center',
                fontsize=8,
                fontweight='bold',
                color=text_color
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