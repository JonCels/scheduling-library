class Schedule:
    def __init__(self, name, schedule_id, start_date, end_date):
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
        if op.resource_type != resource.resource_type:
            raise ValueError(f"Operation resource_type '{op.resource_type}' does not match resource '{resource.resource_type}'")

        end_time = start_time + op.duration

        # Resource available
        if not resource.is_available(start_time, end_time):
            return False

        # Assign scheduling info
        op.resource_id = resource_id
        op.start_time = start_time
        op.end_time = end_time

        # Add operation to resource schedule
        success = resource.add_operation(op)
        if not success:
            # Rollback if failed
            op.resource_id = None
            op.start_time = None
            op.end_time = None
            return False

        return True

    