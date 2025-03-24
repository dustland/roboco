"""
Task API Schema

This module defines the Pydantic models for task-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.core.schema import Task as CoreTask


class TaskBase(BaseModel):
    """Base model for task data."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    status: str = Field(default="TODO", description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the task")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for the task")


class TaskCreate(TaskBase):
    """Request model for creating a task."""
    sprint_name: Optional[str] = Field(None, description="Optional sprint to assign this task to")
    due_date: Optional[datetime] = Field(None, description="Due date for the task")


class TaskUpdate(BaseModel):
    """Request model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    sprint_name: Optional[str] = None
    due_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class Task(TaskBase):
    """Response model for a task."""
    id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    sprint_name: Optional[str] = None
    project_id: str
    
    class Config:
        """Pydantic config for the Task model."""
        from_attributes = True
    
    @classmethod
    def from_core_model(cls, task: CoreTask, task_id: str, sprint_name: Optional[str], project_id: str):
        """Create an API Task from a core Task model."""
        return cls(
            id=task_id,
            title=task.title,
            description=task.description,
            status=task.status,
            assigned_to=task.assigned_to,
            priority=task.priority,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            due_date=task.due_date,
            tags=task.tags,
            metadata=task.metadata,
            sprint_name=sprint_name,
            project_id=project_id
        )
