"""
Project API Schema

This module defines the Pydantic models for project-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.api.schemas.task import Task
from roboco.core.schema import ProjectConfig as CoreProjectConfig


class ProjectBase(BaseModel):
    """Base model for project data."""
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Description of the project goals")
    teams: List[str] = Field(default_factory=list, description="Teams involved in this project")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the project")


class ProjectCreate(ProjectBase):
    """Request model for creating a project."""
    directory: Optional[str] = Field(None, description="Directory where project files should be stored")
    source_code_dir: str = Field(default="src", description="Directory for source code within the project directory")
    docs_dir: str = Field(default="docs", description="Directory for documentation within the project directory")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    teams: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class Project(ProjectBase):
    """Response model for a project."""
    id: str
    created_at: datetime
    updated_at: datetime
    directory: str
    jobs: List[str] = []
    tasks: List[Task] = []
    source_code_dir: str
    docs_dir: str
    
    class Config:
        """Pydantic config for the Project model."""
        from_attributes = True
    
    @classmethod
    def from_core_model(cls, project: CoreProjectConfig, project_id: str):
        """Create an API Project from a core ProjectConfig model."""
        from roboco.api.schemas.task import Task
        
        # Convert tasks
        tasks = [
            Task(
                id=task.id,
                title=task.title,
                description=task.description,
                status=task.status,
                assigned_to=task.assigned_to,
                priority=task.priority,
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                due_date=getattr(task, 'due_date', None),
                tags=task.tags,
                metadata=getattr(task, 'metadata', {}),
                sprint_name=None,
                project_id=project_id
            )
            for task in project.tasks
        ]
        
        return cls(
            id=project_id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            directory=project.directory,
            teams=project.teams,
            jobs=project.jobs,
            tasks=tasks,
            tags=project.tags,
            source_code_dir=project.source_code_dir,
            docs_dir=project.docs_dir
        )
