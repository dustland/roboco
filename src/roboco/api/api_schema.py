"""
API Schema Definitions

This module defines the Pydantic model schemas used by the RoboCo API.
It extends or adapts models from the core schema where appropriate.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.core.schema import TodoItem as CoreTodoItem, Sprint as CoreSprint, ProjectConfig


class JobRequest(BaseModel):
    """Request model for creating a new job."""
    team: str
    query: str
    initial_agent: Optional[str] = None
    output_dir: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    project_id: Optional[str] = None


class JobStatus(BaseModel):
    """Status of a running or completed job."""
    job_id: str
    team: str
    status: str = Field(..., description="Current status (running, completed, failed)")
    start_time: datetime
    end_time: Optional[datetime] = None
    last_updated: datetime
    output_dir: str
    initial_agent: str
    query: str
    current_agent: Optional[str] = None
    progress: Optional[float] = Field(None, description="Progress from 0.0 to 1.0")
    error: Optional[str] = None
    result: Optional[Any] = None
    project_id: Optional[str] = None


class TeamInfo(BaseModel):
    """Information about an available team."""
    key: str
    name: str
    description: str
    roles: List[str]
    tools: List[str]


class ArtifactInfo(BaseModel):
    """Information about a generated artifact."""
    name: str
    path: str
    size: int
    last_modified: datetime
    type: str = Field(..., description="Type of artifact (file or directory)")


class ToolRegistration(BaseModel):
    """Information for registering a tool with an agent."""
    tool_name: str
    agent_name: str
    parameters: Optional[Dict[str, Any]] = None


class AgentStatusUpdate(BaseModel):
    """Update for a job's current agent and progress."""
    job_id: str
    current_agent: str
    progress: Optional[float] = None
    status_message: Optional[str] = None


# API-specific request/response models for Todo management

class TodoItemCreate(BaseModel):
    """Request model for creating a todo item."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    status: str = Field(default="TODO", description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    depends_on: List[str] = Field(default_factory=list, description="IDs of tasks this task depends on")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the task")
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


class TodoItem(BaseModel):
    """Response model for a todo item."""
    id: str
    title: str
    description: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    priority: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    depends_on: List[str] = []
    tags: List[str] = []
    sprint_name: Optional[str] = None
    project_id: str
    
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


# API-specific request/response models for Sprint management

class SprintCreate(BaseModel):
    """Request model for creating a sprint."""
    name: str = Field(..., description="Name of the sprint")
    description: Optional[str] = Field(None, description="Description of the sprint goals")
    start_date: datetime = Field(..., description="Start date of the sprint")
    end_date: datetime = Field(..., description="End date of the sprint")
    status: str = Field(default="planned", description="Status of the sprint (planned, active, completed)")


class SprintUpdate(BaseModel):
    """Request model for updating a sprint."""
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None


class Sprint(BaseModel):
    """Response model for a sprint."""
    name: str
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    status: str
    todos: List[TodoItem] = []
    project_id: str
    
    @classmethod
    def from_core_model(cls, sprint: CoreSprint, project_id: str, todos: Optional[List[TodoItem]] = None):
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


# API-specific request/response models for Project management

class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Description of the project goals")
    directory: Optional[str] = Field(None, description="Directory where project files should be stored")
    teams: List[str] = Field(default_factory=list, description="Teams involved in this project")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the project")
    source_code_dir: str = Field(default="src", description="Directory for source code within the project directory")
    docs_dir: str = Field(default="docs", description="Directory for documentation within the project directory")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = None
    description: Optional[str] = None
    teams: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    current_sprint: Optional[str] = None


class Project(BaseModel):
    """Response model for a project."""
    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    directory: str
    teams: List[str] = []
    jobs: List[str] = []
    sprints: List[Sprint] = []
    current_sprint: Optional[str] = None
    todos: List[TodoItem] = []
    tags: List[str] = []
    source_code_dir: str
    docs_dir: str
    
    @classmethod
    def from_core_model(cls, project: ProjectConfig, project_id: str):
        """Create an API Project from a core ProjectConfig model."""
        # Convert todos to API model
        todos = [
            TodoItem.from_core_model(
                todo=todo,
                todo_id=f"{project_id}_backlog_{i}",
                sprint_name=None,
                project_id=project_id
            )
            for i, todo in enumerate(project.todos)
        ]
        
        # Convert sprints to API model
        sprints = []
        for sprint in project.sprints:
            sprint_todos = [
                TodoItem.from_core_model(
                    todo=todo,
                    todo_id=f"{project_id}_{sprint.name}_{i}",
                    sprint_name=sprint.name,
                    project_id=project_id
                )
                for i, todo in enumerate(sprint.todos)
            ]
            sprints.append(Sprint.from_core_model(
                sprint=sprint,
                project_id=project_id,
                todos=sprint_todos
            ))
        
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