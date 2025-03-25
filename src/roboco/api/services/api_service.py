"""
API Service

This module provides services for the API layer, orchestrating interactions between
the API endpoints and the domain services.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
import os

from roboco.api.models.job import JobRequest
from roboco.services.project_service import ProjectService
from roboco.services.team_service import TeamService
from roboco.services.agent_service import AgentService
from roboco.services.workspace_service import WorkspaceService
from roboco.services.chat_service import ChatService
from roboco.storage.adapters.pydantic_adapters import (
    project_to_pydantic, pydantic_to_project,
    task_to_pydantic, pydantic_to_task
)
from roboco.core.schema import ProjectConfig, Task as PydanticTask
from roboco.api.schemas.project import Project as ApiProject, ProjectCreate, ProjectUpdate
from roboco.api.schemas.task import Task as ApiTask, TaskCreate, TaskUpdate
from roboco.api.schemas.chat import ChatRequest, ChatResponse
from roboco.storage.repositories.file_project_repository import FileProjectRepository


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
            workspace_service: Service for workspace-related operations
            chat_service: Service for chat-related operations
            project_repository: Optional repository to use for sprint service
        """
        self.project_service = project_service
        self.team_service = team_service or TeamService()
        self.agent_service = agent_service or AgentService()
        
        # If project_repository is not provided, try to get it from the router's dependency injection
        if project_repository is None:
            project_repository = FileProjectRepository()
            
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
    
    async def create_task(self, project_id: str, task_create: TaskCreate) -> ApiTask:
        """Create a new task.
        
        Args:
            project_id: ID of the project to create the task in
            task_create: Task creation data
            
        Returns:
            The created task in API format
        """
        # Create the task using the domain service
        task_id = await self.project_service.create_task(
            project_id=project_id,
            title=task_create.title,
            description=task_create.description,
            priority=task_create.priority,
            assigned_to=task_create.assigned_to
        )
        
        # Get the created task
        domain_task = await self.project_service.get_task(project_id, task_id)
        
        # Convert domain task to API task
        pydantic_task = task_to_pydantic(domain_task)
        api_task = ApiTask.from_core_model(pydantic_task, domain_task.id)
        
        return api_task
    
    async def update_task(self, project_id: str, task_id: str, task_update: TaskUpdate) -> ApiTask:
        """Update a task.
        
        Args:
            project_id: ID of the project containing the task
            task_id: ID of the task to update
            task_update: Task update data
            
        Returns:
            The updated task in API format
            
        Raises:
            ValueError: If the task does not exist
        """
        # Get the existing task
        domain_task = await self.project_service.get_task(project_id, task_id)
        
        if not domain_task:
            raise ValueError(f"Task with ID {task_id} does not exist in project {project_id}")
        
        # Update the task fields
        if task_update.title is not None:
            domain_task.title = task_update.title
        
        if task_update.description is not None:
            domain_task.description = task_update.description
        
        if task_update.priority is not None:
            domain_task.priority = task_update.priority
        
        if task_update.assigned_to is not None:
            domain_task.assigned_to = task_update.assigned_to
        
        if task_update.status is not None:
            domain_task.status = task_update.status
        
        # Update the task using the domain service
        await self.project_service.update_task(project_id, domain_task)
        
        # Get the updated task
        updated_domain_task = await self.project_service.get_task(project_id, task_id)
        
        # Convert domain task to API task
        pydantic_task = task_to_pydantic(updated_domain_task)
        api_task = ApiTask.from_core_model(pydantic_task, updated_domain_task.id)
        
        return api_task
    
    async def delete_task(self, project_id: str, task_id: str) -> bool:
        """Delete a task.
        
        Args:
            project_id: ID of the project containing the task
            task_id: ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
        """
        return await self.project_service.delete_task(project_id, task_id)
    
    async def list_tasks(self, project_id: str) -> List[ApiTask]:
        """List all tasks in a project.
        
        Args:
            project_id: ID of the project to list tasks from
            
        Returns:
            List of tasks in API format
        """
        domain_tasks = await self.project_service.list_tasks(project_id)
        
        # Convert domain tasks to API tasks
        api_tasks = []
        for task in domain_tasks:
            # First convert to Pydantic model (intermediate step)
            pydantic_task = task_to_pydantic(task)
            
            # Then convert to API model
            api_task = ApiTask.from_core_model(pydantic_task, task.id)
            api_tasks.append(api_task)
        
        return api_tasks
    
    # Team-related methods
    
    async def list_teams(self) -> List[Dict[str, Any]]:
        """
        List all available teams.
        
        Returns:
            List of team information dictionaries.
        """
        return await self.team_service.list_teams()
    
    async def get_team(self, team_key: str) -> Dict[str, Any]:
        """
        Get details for a specific team.
        
        Args:
            team_key: The unique identifier for the team.
            
        Returns:
            Team information dictionary.
        """
        return await self.team_service.get_team(team_key)
    
    # Job-related methods
    
    async def create_job(self, job_request: JobRequest) -> Dict[str, Any]:
        """
        Create a new job.
        
        Args:
            job_request: Job request data.
            
        Returns:
            Job status dictionary.
        """
        return await self.team_service.create_job(
            team_key=job_request.team,
            query=job_request.query,
            initial_agent=job_request.initial_agent,
            output_dir=job_request.output_dir,
            parameters=job_request.parameters,
            project_id=job_request.project_id
        )
    
    async def run_job(self, job_id: str) -> None:
        """
        Run a job in the background.
        
        Args:
            job_id: The ID of the job to run.
        """
        await self.team_service.run_job(job_id)
    
    async def list_jobs(self, status_filter: Optional[str] = None, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status or project ID.
        
        Args:
            status_filter: Optional status to filter by.
            project_id: Optional project ID to filter by.
            
        Returns:
            List of job status dictionaries.
        """
        return await self.team_service.list_jobs(status_filter, project_id)
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific job.
        
        Args:
            job_id: The ID of the job.
            
        Returns:
            Job status dictionary.
        """
        job_status = await self.team_service.get_job_status(job_id)
        if not job_status:
            raise ValueError(f"Job '{job_id}' not found")
        return job_status
    
    async def update_job_status(self, job_id: str, update: AgentStatusUpdate) -> Dict[str, Any]:
        """
        Update the status of a job.
        
        Args:
            job_id: The ID of the job.
            update: Status update data.
            
        Returns:
            Updated job status dictionary.
        """
        return await self.team_service.update_job_status(
            job_id=job_id,
            current_agent=update.current_agent,
            progress=update.progress,
            status_message=update.status_message
        )
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: The ID of the job to cancel.
            
        Returns:
            True if the job was cancelled, False if not found or already completed.
        """
        return await self.team_service.cancel_job(job_id)
    
    async def list_job_artifacts(self, job_id: str, path: str = "") -> List[Dict[str, Any]]:
        """
        List artifacts for a specific job.
        
        Args:
            job_id: The ID of the job.
            path: Optional path within the job directory.
            
        Returns:
            List of artifact information dictionaries.
        """
        return await self.team_service.list_job_artifacts(job_id, path)
    
    async def get_job_artifact(self, job_id: str, artifact_path: str) -> str:
        """
        Get the path to a specific artifact file.
        
        Args:
            job_id: The ID of the job.
            artifact_path: Path to the artifact within the job directory.
            
        Returns:
            Full path to the artifact file.
        """
        return await self.team_service.get_job_artifact(job_id, artifact_path)
    
    async def register_tool(self, job_id: str, registration: ToolRegistration) -> bool:
        """
        Register a tool with an agent for a specific job.
        
        Args:
            job_id: The ID of the job.
            registration: Tool registration data.
            
        Returns:
            True if successful.
        """
        return await self.team_service.register_tool(
            job_id=job_id,
            tool_name=registration.tool_name,
            agent_name=registration.agent_name,
            parameters=registration.parameters
        )
    
    # Agent-related methods
    
    async def list_agent_types(self) -> List[Dict[str, Any]]:
        """
        List all available agent types.
        
        Returns:
            List of agent type information dictionaries.
        """
        return await self.agent_service.list_agent_types()
    
    async def get_agent_type(self, name: str) -> Dict[str, Any]:
        """
        Get details for a specific agent type.
        
        Args:
            name: The name of the agent type.
            
        Returns:
            Agent type information dictionary.
        """
        return await self.agent_service.get_agent_type(name)
    
    async def chat_with_project_agent(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Initiate or continue a chat with the project agent.
        
        Args:
            chat_request: Chat request data.
            
        Returns:
            Chat response with conversation ID and any created project details.
        """
        # Create a new conversation if no ID provided
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Use the chat service for chat operations
        return await self.chat_service.chat_with_project_agent(chat_request)
    
    # Workspace-related methods
    
    async def create_workspace(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new workspace.
        
        Args:
            name: Name of the workspace
            description: Optional description
            
        Returns:
            Dictionary with workspace information
        """
        return await self.workspace_service.create_workspace(name, description)
    
    async def get_workspace(self, workspace_id_or_name: str) -> Dict[str, Any]:
        """
        Get workspace information.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            
        Returns:
            Dictionary with workspace information
        """
        return await self.workspace_service.get_workspace(workspace_id_or_name)
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all workspaces.
        
        Returns:
            List of dictionaries with workspace information
        """
        return await self.workspace_service.list_workspaces()
    
    async def update_workspace(self, workspace_id_or_name: str, 
                              name: Optional[str] = None,
                              description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update workspace information.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            name: Optional new name
            description: Optional new description
            
        Returns:
            Dictionary with updated workspace information
        """
        return await self.workspace_service.update_workspace(workspace_id_or_name, name, description)
    
    async def delete_workspace(self, workspace_id_or_name: str) -> bool:
        """
        Delete a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            
        Returns:
            True if the workspace was deleted, False otherwise
        """
        return await self.workspace_service.delete_workspace(workspace_id_or_name)
    
    async def save_artifact(self, workspace_id_or_name: str, 
                           artifact_name: str, 
                           content: Union[str, bytes, Any],
                           artifact_type: str = "text",
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save an artifact to a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_name: Name of the artifact
            content: Content of the artifact
            artifact_type: Type of the artifact
            metadata: Optional metadata for the artifact
            
        Returns:
            Dictionary with artifact information
        """
        return await self.workspace_service.save_artifact(
            workspace_id_or_name, 
            artifact_name, 
            content, 
            artifact_type, 
            metadata
        )
    
    async def get_artifact(self, workspace_id_or_name: str, artifact_id_or_name: str) -> Dict[str, Any]:
        """
        Get an artifact from a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_id_or_name: ID or name of the artifact
            
        Returns:
            Dictionary with artifact information and content
        """
        return await self.workspace_service.get_artifact(workspace_id_or_name, artifact_id_or_name)
    
    async def list_artifacts(self, workspace_id_or_name: str, 
                            artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all artifacts in a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_type: Optional type to filter by
            
        Returns:
            List of dictionaries with artifact information
        """
        return await self.workspace_service.list_artifacts(workspace_id_or_name, artifact_type)
    
    async def delete_artifact(self, workspace_id_or_name: str, artifact_id_or_name: str) -> bool:
        """
        Delete an artifact from a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_id_or_name: ID or name of the artifact
            
        Returns:
            True if the artifact was deleted, False otherwise
        """
        return await self.workspace_service.delete_artifact(workspace_id_or_name, artifact_id_or_name)
