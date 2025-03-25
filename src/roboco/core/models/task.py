"""
Task schema definitions.
"""
from enum import Enum
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


class Task(BaseModel):
    """A single task in a project or todo list."""
    description: str = Field(..., description="Description of the task to complete")
    expected_outcome: Optional[str] = Field(None, description="Expected outcome of the task")
    status: str = Field(default="TODO", description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    created_at: datetime = Field(default_factory=datetime.now, description="When the task was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the task was last updated")
    completed_at: Optional[datetime] = Field(None, description="When the task was completed")
    depends_on: List[str] = Field(default_factory=list, description="IDs of tasks this task depends on")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the task")
