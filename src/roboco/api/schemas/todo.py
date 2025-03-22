"""
Todo API Schema

This module defines the Pydantic models for todo-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.core.schema import TodoItem as CoreTodoItem


class TodoItemBase(BaseModel):
    """Base model for todo item data."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    status: str = Field(default="TODO", description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    depends_on: List[str] = Field(default_factory=list, description="IDs of tasks this task depends on")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the task")


class TodoItemCreate(TodoItemBase):
    """Request model for creating a todo item."""
    sprint_name: Optional[str] = Field(None, description="Optional sprint to assign this task to")


class TodoItemUpdate(BaseModel):
    """Request model for updating a todo item."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: Optional[str] = None
    depends_on: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    sprint_name: Optional[str] = None


class TodoItem(TodoItemBase):
    """Response model for a todo item."""
    id: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    sprint_name: Optional[str] = None
    project_id: str
    
    class Config:
        """Pydantic config for the TodoItem model."""
        from_attributes = True
    
    @classmethod
    def from_core_model(cls, todo: CoreTodoItem, todo_id: str, sprint_name: Optional[str], project_id: str):
        """Create an API TodoItem from a core TodoItem model."""
        return cls(
            id=todo_id,
            title=todo.title,
            description=todo.description,
            status=todo.status,
            assigned_to=todo.assigned_to,
            priority=todo.priority,
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            completed_at=todo.completed_at,
            depends_on=todo.depends_on,
            tags=todo.tags,
            sprint_name=sprint_name,
            project_id=project_id
        )
