"""
API Service

This module provides services for the API layer, orchestrating interactions between
the API endpoints and the domain services.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
import os
from loguru import logger

from roboco.services.project_service import ProjectService
from roboco.services.team_service import TeamService
from roboco.services.agent_service import AgentService
from roboco.services.task_service import TaskService
from roboco.services.workspace_service import WorkspaceService
from roboco.services.chat_service import ChatService
from roboco.infrastructure.adapters.pydantic_adapters import (
    project_to_pydantic, pydantic_to_project
)
from roboco.core.schema import ProjectConfig, Task
from roboco.api.models.project import Project as ApiProject, ProjectCreate, ProjectUpdate
from roboco.api.models.task import Task as ApiTask, TaskCreate, TaskUpdate

class ApiService:
    """Service for API operations.
    
    This service acts as a facade for the API layer, orchestrating interactions
    between the API endpoints and the domain services.
    
    It follows the Dependency Injection pattern, accepting service dependencies
    through the constructor rather than creating them directly.
    """
    
    def __init__(
        self, 
        project_service: ProjectService,
        team_service: Optional[TeamService] = None,
        agent_service: Optional[AgentService] = None,
        task_service: Optional[TaskService] = None,
        workspace_service: Optional[WorkspaceService] = None,
        chat_service: Optional[ChatService] = None,
        project_repository = None
    ):
        """
        Initialize the API service with its dependencies.
        
        Args:
            project_service: Service for project-related operations
            team_service: Service for team-related operations
            agent_service: Service for agent-related operations
            task_service: Service for task-related operations
            workspace_service: Service for workspace-related operations
            chat_service: Service for chat-related operations
            project_repository: Optional repository to use for task service
        """
        self.project_service = project_service
        self.team_service = team_service or TeamService()
        self.agent_service = agent_service or AgentService()
        
        # If project_repository is not provided, try to get it from the router's dependency injection
        if project_repository is None:
            from roboco.infrastructure.repositories.file_project_repository import FileProjectRepository
            project_repository = FileProjectRepository()
            
        self.task_service = task_service or TaskService(project_repository)
        self.workspace_service = workspace_service or WorkspaceService()
        self.chat_service = chat_service or ChatService(project_repository)
        
        # Set up workspace directory
        self.workspace_dir = os.path.expanduser("~/roboco_workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)

    async def list_projects(self) -> List[ApiProject]:
        """List all projects.
        
        Returns:
            List of all projects in API format
        """
        domain_projects = await self.project_service.list_projects()
        
        # Convert domain projects to API projects
        api_projects = []
        for project in domain_projects:
            # First convert to Pydantic model (intermediate step)
            pydantic_project = project_to_pydantic(project)
            
            # Then convert to API model
            api_project = ApiProject.from_core_model(pydantic_project, project.id)
            api_projects.append(api_project)
        
        return api_projects
    
    async def get_project(self, project_id: str) -> Optional[ApiProject]:
        """Get a project by its ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            The project in API format if found, None otherwise
        """
        domain_project = await self.project_service.get_project(project_id)
        
        if not domain_project:
            return None
            
        # Convert domain project to API project
        pydantic_project = project_to_pydantic(domain_project)
        api_project = ApiProject.from_core_model(pydantic_project, domain_project.id)
        
        return api_project
    
    async def create_project(self, project_create: ProjectCreate) -> ApiProject:
        """Create a new project.
        
        Args:
            project_create: Project creation data
            
        Returns:
            The created project in API format
        """
        # Create the project using the domain service
        project_id = await self.project_service.create_project(
            name=project_create.name,
            description=project_create.description,
            directory=project_create.directory,
            teams=project_create.teams,
            tags=project_create.tags
        )
        
        # Get the created project
        domain_project = await self.project_service.get_project(project_id)
        
        # Convert domain project to API project
        pydantic_project = project_to_pydantic(domain_project)
        api_project = ApiProject.from_core_model(pydantic_project, domain_project.id)
        
        return api_project
    
    async def update_project(self, project_id: str, project_update: ProjectUpdate) -> ApiProject:
        """Update a project.
        
        Args:
            project_id: ID of the project to update
            project_update: Project update data
            
        Returns:
            The updated project in API format
            
        Raises:
            ValueError: If the project does not exist
        """
        # Get the existing project
        domain_project = await self.project_service.get_project(project_id)
        
        if not domain_project:
            raise ValueError(f"Project with ID {project_id} does not exist")
        
        # Update the project fields
        if project_update.name is not None:
            domain_project.name = project_update.name
        
        if project_update.description is not None:
            domain_project.description = project_update.description
        
        if project_update.teams is not None:
            domain_project.teams = project_update.teams
        
        if project_update.tags is not None:
            domain_project.tags = project_update.tags
        
        # Update the project using the domain service
        await self.project_service.update_project(domain_project)
        
        # Get the updated project
        updated_domain_project = await self.project_service.get_project(project_id)
        
        # Convert domain project to API project
        pydantic_project = project_to_pydantic(updated_domain_project)
        api_project = ApiProject.from_core_model(pydantic_project, updated_domain_project.id)
        
        return api_project
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        return await self.project_service.delete_project(project_id)
        
    # Task-related methods
    
    async def list_tasks(self, project_id: str) -> List[ApiTask]:
        """List all tasks for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of all tasks for the project in API format
            
        Raises:
            ValueError: If the project does not exist
        """
        tasks = await self.task_service.get_tasks_for_project(project_id)
        
        # Convert domain tasks to API tasks
        api_tasks = [ApiTask.from_core_model(task, project_id) for task in tasks]
        
        return api_tasks
    
    async def get_task(self, project_id: str, task_id: str) -> Optional[ApiTask]:
        """Get a task by its ID.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to retrieve
            
        Returns:
            The task in API format if found, None otherwise
            
        Raises:
            ValueError: If the project does not exist
        """
        task = await self.task_service.get_task(project_id, task_id)
        
        if not task:
            return None
            
        # Convert domain task to API task
        api_task = ApiTask.from_core_model(task, project_id)
        
        return api_task
    
    async def create_task(self, project_id: str, task_create: TaskCreate) -> ApiTask:
        """Create a new task.
        
        Args:
            project_id: ID of the project
            task_create: Task creation data
            
        Returns:
            The created task in API format
            
        Raises:
            ValueError: If the project does not exist
        """
        # Create the task using the domain service
        task = await self.task_service.create_task(
            project_id=project_id,
            title=task_create.title,
            description=task_create.description,
            status=task_create.status,
            assigned_to=task_create.assigned_to,
            priority=task_create.priority,
            depends_on=task_create.depends_on,
            tags=task_create.tags
        )
        
        # Convert domain task to API task
        api_task = ApiTask.from_core_model(task, project_id)
        
        return api_task
    
    async def update_task(self, project_id: str, task_id: str, task_update: TaskUpdate) -> ApiTask:
        """Update a task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to update
            task_update: Task update data
            
        Returns:
            The updated task in API format
            
        Raises:
            ValueError: If the project or task does not exist
        """
        # Update the task using the domain service
        task = await self.task_service.update_task(
            project_id=project_id,
            task_id=task_id,
            title=task_update.title,
            description=task_update.description,
            status=task_update.status,
            assigned_to=task_update.assigned_to,
            priority=task_update.priority,
            depends_on=task_update.depends_on,
            tags=task_update.tags
        )
        
        # Convert domain task to API task
        api_task = ApiTask.from_core_model(task, project_id)
        
        return api_task
    
    async def delete_task(self, project_id: str, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
            
        Raises:
            ValueError: If the project does not exist
        """
        return await self.task_service.delete_task(project_id, task_id)
