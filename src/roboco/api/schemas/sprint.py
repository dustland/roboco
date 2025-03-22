"""
Sprint API Schema

This module defines the Pydantic models for sprint-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.core.schema import Sprint as CoreSprint


class SprintBase(BaseModel):
    """Base model for sprint data."""
    name: str = Field(..., description="Name of the sprint")
    description: Optional[str] = Field(None, description="Description of the sprint goals")
    start_date: datetime = Field(..., description="Start date of the sprint")
    end_date: datetime = Field(..., description="End date of the sprint")
    status: str = Field(default="planned", description="Status of the sprint (planned, active, completed)")


class SprintCreate(SprintBase):
    """Request model for creating a sprint."""
    pass


class SprintUpdate(BaseModel):
    """Request model for updating a sprint."""
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class Sprint(SprintBase):
    """Response model for a sprint."""
    todos: List["TodoItem"] = []
    project_id: str
    
    class Config:
        """Pydantic config for the Sprint model."""
        from_attributes = True
    
    @classmethod
    def from_core_model(cls, sprint: CoreSprint, project_id: str, todos: Optional[List["TodoItem"]] = None):
        """Create an API Sprint from a core Sprint model."""
        return cls(
            name=sprint.name,
            description=sprint.description,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
            status=sprint.status,
            todos=todos or [],
            project_id=project_id
        )


# Import at the end to avoid circular imports
from roboco.api.schemas.todo import TodoItem
Sprint.update_forward_refs()
