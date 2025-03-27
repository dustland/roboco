"""
Project API Schema

This module defines the Pydantic models for project-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.api.models.task import Task
from roboco.core.models.project_manifest import ProjectManifest

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
    name: Optional[str] = Field(None, description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project goals")
    teams: Optional[List[str]] = Field(None, description="Teams involved in this project")
    tags: Optional[List[str]] = Field(None, description="Tags for categorizing the project")
    source_code_dir: Optional[str] = Field(None, description="Directory for source code within the project directory")
    docs_dir: Optional[str] = Field(None, description="Directory for documentation within the project directory")


class Project(ProjectBase):
    """Response model for a project."""
    id: str
    created_at: str
    updated_at: str
    directory: str
    jobs: List[str] = []
    tasks: List[Task] = []
    source_code_dir: str
    docs_dir: str
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True

    @classmethod
    def from_core_model(cls, project: ProjectManifest) -> 'Project':
        """Create an API Project from a core Project model.
        
        Args:
            project: Core project model
            
        Returns:
            API Project model
        """
        # Convert core tasks to API tasks
        tasks = []
        for task in project.tasks:
            tasks.append(Task(
                id=getattr(task, 'id', str(len(tasks))),
                description=task.description,
                status=task.status,
                assigned_to=task.assigned_to,
                priority=task.priority,
                depends_on=task.depends_on or [],
                created_at=task.created_at,
                updated_at=task.updated_at,
                completed_at=task.completed_at,
                project_id=project.id
            ))
        
        return cls(
            id=project.id,
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
            docs_dir=project.docs_dir,
            metadata=project.metadata
        )
