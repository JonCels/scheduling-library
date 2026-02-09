"""
OperationTemplate class for the scheduling library.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass(frozen=True)
class OperationTemplate:
    """
    Defines a reusable operation within a job template.
    """
    template_id: str
    duration: float
    resource_type: Optional[str] = None
    possible_resource_ids: Optional[List[str]] = None
    resource_requirements: Optional[List[Dict[str, List[str]]]] = None
    precedence: List[str] = field(default_factory=list)
    metadata: Optional[dict] = None
