"""
JobTemplate class for the scheduling library.

A JobTemplate defines a reusable set of operations and precedence constraints.
It can be instantiated into concrete Job instances with unique operation IDs.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from job import Job
from operation import Operation


@dataclass(frozen=True)
class OperationTemplate:
    """
    Defines a reusable operation within a job template.
    """
    template_id: str
    duration: float
    resource_type: str
    possible_resource_ids: List[str]
    precedence: List[str] = field(default_factory=list)
    metadata: Optional[dict] = None


class JobTemplate:
    """
    Represents a reusable job definition with optional blocking constraint.
    """

    def __init__(
        self,
        template_id: str,
        operations: List[OperationTemplate],
        metadata: Optional[dict] = None,
        blocking: bool = False,
    ):
        self.template_id = template_id
        self.operations = operations
        self.metadata = metadata or {}
        self.blocking = blocking

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
                    possible_resource_ids=list(op.possible_resource_ids),
                    precedence=precedence,
                    metadata=op.metadata or {},
                )
            )

        return Job(job_id, operations, metadata=self.metadata.copy())
