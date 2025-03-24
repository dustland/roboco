"""
Task API Schema

This module defines the Pydantic models for task-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

from roboco.core.schema import Task as CoreTask


class TaskBase(BaseModel):
    """Base model for task data."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    status: str = Field(default="TODO", description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    depends_on: List[str] = Field(default_factory=list, description="IDs of tasks this task depends on")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the task")


class TaskCreate(TaskBase):
    """Request model for creating a task."""
    pass


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = Field(None, description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    status: Optional[str] = Field(None, description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: Optional[str] = Field(None, description="Priority level (low, medium, high, critical)")
    depends_on: Optional[List[str]] = Field(None, description="IDs of tasks this task depends on")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing the task")


class Task(TaskBase):
    """Response model for a task."""
    id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    project_id: str

    class Config:
        from_attributes = True

    @classmethod
    def from_core_model(cls, task: CoreTask, project_id: str) -> 'Task':
        """Create an API Task from a core Task model.
        
        Args:
            task: Core task model
            project_id: ID of the project this task belongs to
            
        Returns:
            API Task model
        """
        return cls(
            id=getattr(task, 'id', str(uuid.uuid4())),
            title=task.title,
            description=task.description,
            status=task.status,
            assigned_to=task.assigned_to,
            priority=task.priority,
            depends_on=task.depends_on or [],
            tags=task.tags or [],
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            project_id=project_id
        )
