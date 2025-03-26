"""
API Service

This module provides services for the API layer, orchestrating interactions between
the API endpoints and the domain services.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
import os
from roboco.core.logger import get_logger

logger = get_logger(__name__)

from roboco.services.project_service import ProjectService
from roboco.services.agent_service import AgentService
from roboco.services.chat_service import ChatService
from roboco.api.models.project import Project as ApiProject, ProjectCreate, ProjectUpdate
from roboco.api.models.task import Task as ApiTask, TaskCreate, TaskUpdate
from roboco.core.models.chat import ChatRequest, ChatResponse
from roboco.core.project_fs import ProjectFS
from roboco.core.config import load_config

def project_to_pydantic(project):
    """Convert domain project to Pydantic model."""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "directory": project.directory,
        "teams": project.teams,
        "tags": project.tags,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }

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
        agent_service: Optional[AgentService] = None,
        chat_service: Optional[ChatService] = None
    ):
        """
        Initialize the API service with its dependencies.
        
        Args:
            project_service: Service for project-related operations
            agent_service: Service for agent-related operations
            chat_service: Service for chat-related operations
        """
        self.project_service = project_service
        self.agent_service = agent_service or AgentService()
        
        # Create services with default implementations if not provided
        self.chat_service = chat_service or ChatService()
        
        # Let the ProjectFS/FileSystem handle workspace paths
        self.workspace_dir = ""
        config = load_config()
        os.makedirs(os.path.join(config.workspace_root, self.workspace_dir), exist_ok=True)

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
    
    async def start_chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Process a chat request with the project agent.
        
        Args:
            chat_request: The chat request containing the query and other parameters
            
        Returns:
            ChatResponse object with the response details
        """
        return await self.chat_service.start_chat(chat_request)
        
    async def get_chat_status(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a chat conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary with conversation details or None if not found
        """
        conversation = await self.chat_service.get_conversation_history(conversation_id)
        
        if not conversation:
            return None
            
        # Format the response
        messages = conversation.get("messages", [])
        latest_message = messages[-1] if messages else {"content": "", "role": "assistant"}
        
        return {
            "conversation_id": conversation_id,
            "project_id": conversation.get("project_id"),
            "message": latest_message.get("content", ""),
            "project_details": None,  # Add project details if needed
            "status": "completed"
        }
