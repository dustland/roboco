"""
Task API Models

This module defines the Pydantic models for task-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from roboco.core.models.task import Task, TaskStatus


class TaskCreate(BaseModel):
    """API model for creating a task."""
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.TODO
    project_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    def to_db_model(self) -> Task:
        """Convert API model to database model."""
        data = self.model_dump(exclude_unset=True)
        return Task(**data)


class TaskUpdate(BaseModel):
    """API model for updating a task."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    meta: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """API model for task responses."""
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    project_id: Optional[str] = None
    created_at: str
    updated_at: str
    completed_at: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    
    @classmethod
    def from_db_model(cls, task: Task) -> "TaskResponse":
        """Convert database model to API response model."""
        return cls(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status,
            project_id=task.project_id,
            created_at=task.created_at.isoformat() if task.created_at else None,
            updated_at=task.updated_at.isoformat() if task.updated_at else None,
            completed_at=task.completed_at.isoformat() if task.completed_at else None,
            meta=task.meta,
            tags=task.tags
        ) 