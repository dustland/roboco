"""
Phase model definitions.
"""
from typing import List

from pydantic import BaseModel

from roboco.core.models.task import Task
from roboco.core.value_objects.phase_status import PhaseStatus


class Phase(BaseModel):
    """Represents a phase in the task list."""
    name: str
    tasks: List[Task]
    status: PhaseStatus = PhaseStatus.TODO
