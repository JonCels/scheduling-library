"""
JobTemplate class for the scheduling library.

A JobTemplate defines a reusable set of operations and precedence constraints.
It can be instantiated into concrete Job instances with unique operation IDs.
"""

from typing import List, Optional

from classes.job import Job
from classes.operation import Operation
from classes.operation_template import OperationTemplate


class JobTemplate:
    """
    Represents a reusable job definition.
    """

    def __init__(
        self,
        template_id: str,
        operations: List[OperationTemplate],
        metadata: Optional[dict] = None,
    ):
        self.template_id = template_id
        self.operations = operations
        self.metadata = metadata or {}

    def instantiate(self, instance_id: str, job_id: Optional[str] = None) -> Job:
        """
        Create a concrete Job from this template with unique operation IDs.
        """
        job_id = job_id or f"{self.template_id}_{instance_id}"

        id_map = {op.template_id: f"{job_id}_{op.template_id}" for op in self.operations}

        operations = []
        for op in self.operations:
            op_id = id_map[op.template_id]
            precedence = [id_map[p] for p in op.precedence]
            operations.append(
                Operation(
                    operation_id=op_id,
                    job_id=job_id,
                    duration=op.duration,
                    resource_type=op.resource_type,
                    possible_resource_ids=list(op.possible_resource_ids)
                    if op.possible_resource_ids
                    else None,
                    resource_requirements=op.resource_requirements,
                    precedence=precedence,
                    metadata=op.metadata or {},
                )
            )

        return Job(job_id, operations, metadata=self.metadata.copy())
