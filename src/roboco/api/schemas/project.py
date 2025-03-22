"""
Project API Schema

This module defines the Pydantic models for project-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.api.schemas.sprint import Sprint
from roboco.api.schemas.todo import TodoItem
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
    current_sprint: Optional[str] = None


class Project(ProjectBase):
    """Response model for a project."""
    id: str
    created_at: datetime
    updated_at: datetime
    directory: str
    jobs: List[str] = []
    sprints: List[Sprint] = []
    current_sprint: Optional[str] = None
    todos: List[TodoItem] = []
    source_code_dir: str
    docs_dir: str
    
    class Config:
        """Pydantic config for the Project model."""
        from_attributes = True
    
    @classmethod
    def from_core_model(cls, project: CoreProjectConfig, project_id: str):
        """Create an API Project from a core ProjectConfig model."""
        from roboco.api.schemas.sprint import Sprint
        from roboco.api.schemas.todo import TodoItem
        
        # Convert sprints and todos
        sprints = []
        for sprint in project.sprints:
            todos = [
                TodoItem(
                    id=todo.id,
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
                    sprint_name=sprint.name,
                    project_id=project_id
                )
                for todo in sprint.todos
            ]
            
            sprints.append(Sprint(
                name=sprint.name,
                description=sprint.description,
                start_date=sprint.start_date,
                end_date=sprint.end_date,
                status=sprint.status,
                todos=todos,
                project_id=project_id
            ))
        
        # Convert project-level todos
        todos = [
            TodoItem(
                id=todo.id,
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
                sprint_name=None,
                project_id=project_id
            )
            for todo in project.todos
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
            sprints=sprints,
            current_sprint=project.current_sprint,
            todos=todos,
            tags=project.tags,
            source_code_dir=project.source_code_dir,
            docs_dir=project.docs_dir
        )
