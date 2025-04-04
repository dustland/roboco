"""
Project API Models

This module defines the Pydantic models for project-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel

from roboco.core.models.project import Project


class ProjectCreate(BaseModel):
    """API model for creating a project."""
    name: str
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    
    def to_db_model(self) -> Project:
        """Convert API model to database model."""
        data = self.model_dump(exclude_unset=True)
        return Project(**data)


class ProjectUpdate(BaseModel):
    """API model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    """API model for project responses."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str
    updated_at: str
    meta: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_db_model(cls, project: Project) -> "ProjectResponse":
        """Convert database model to API response model."""
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at.isoformat() if project.created_at else None,
            updated_at=project.updated_at.isoformat() if project.updated_at else None,
            meta=project.meta
        ) 