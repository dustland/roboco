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

from roboco.domain.models.project import Project
from roboco.domain.models.sprint import Sprint
from roboco.domain.models.todo_item import TodoItem
from roboco.services.project_service import ProjectService
from roboco.services.team_service import TeamService
from roboco.services.agent_service import AgentService
from roboco.services.sprint_service import SprintService
from roboco.services.workspace_service import WorkspaceService
from roboco.infrastructure.adapters.pydantic_adapters import (
    project_to_pydantic, pydantic_to_project,
    sprint_to_pydantic, pydantic_to_sprint,
    todo_to_pydantic, pydantic_to_todo
)
from roboco.core.schema import ProjectConfig, TodoItem as PydanticTodoItem, Sprint as PydanticSprint
from roboco.api.schemas.project import Project as ApiProject, ProjectCreate, ProjectUpdate
from roboco.api.schemas.sprint import Sprint as ApiSprint, SprintCreate, SprintUpdate
from roboco.api.schemas.todo import TodoItem as ApiTodoItem, TodoItemCreate, TodoItemUpdate
from roboco.api.schemas.job import JobRequest, JobStatus, AgentStatusUpdate, ToolRegistration
from roboco.api.schemas.chat import ChatRequest, ChatResponse


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
        sprint_service: Optional[SprintService] = None,
        workspace_service: Optional[WorkspaceService] = None,
        project_repository = None
    ):
        """
        Initialize the API service with its dependencies.
        
        Args:
            project_service: Service for project-related operations
            team_service: Service for team-related operations
            agent_service: Service for agent-related operations
            sprint_service: Service for sprint-related operations
            workspace_service: Service for workspace-related operations
            project_repository: Optional repository to use for sprint service
        """
        self.project_service = project_service
        self.team_service = team_service or TeamService()
        self.agent_service = agent_service or AgentService()
        
        # If project_repository is not provided, try to get it from the router's dependency injection
        if project_repository is None:
            from roboco.infrastructure.repositories.file_project_repository import FileProjectRepository
            project_repository = FileProjectRepository()
            
        self.sprint_service = sprint_service or SprintService(project_repository)
        self.workspace_service = workspace_service or WorkspaceService()
        
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
        
        if project_update.current_sprint is not None:
            domain_project.current_sprint = project_update.current_sprint
        
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
    
    async def create_sprint(self, project_id: str, sprint_create: SprintCreate) -> ApiSprint:
        """
        Create a new sprint.
        
        Args:
            project_id: ID of the project
            sprint_create: Sprint creation data
            
        Returns:
            API Sprint model
        """
        # Convert dates if provided
        start_date = None
        if sprint_create.start_date:
            start_date = datetime.fromisoformat(sprint_create.start_date)
            
        end_date = None
        if sprint_create.end_date:
            end_date = datetime.fromisoformat(sprint_create.end_date)
        
        # Create the sprint using the sprint service
        sprint = await self.sprint_service.create_sprint(
            project_id=project_id,
            name=sprint_create.name,
            description=sprint_create.description,
            start_date=start_date,
            end_date=end_date,
            status=sprint_create.status or "planned"
        )
        
        # Convert to API model
        pydantic_sprint = sprint_to_pydantic(sprint)
        api_sprint = ApiSprint.from_core_model(pydantic_sprint, project_id)
        
        return api_sprint
    
    async def get_sprint(self, project_id: str, sprint_name: str) -> ApiSprint:
        """
        Get a sprint by name.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            API Sprint model
        """
        # Get the sprint using the sprint service
        sprint = await self.sprint_service.get_sprint(project_id, sprint_name)
        
        # Convert to API model
        pydantic_sprint = sprint_to_pydantic(sprint)
        api_sprint = ApiSprint.from_core_model(pydantic_sprint, project_id)
        
        return api_sprint
    
    async def update_sprint(self, project_id: str, sprint_name: str, sprint_update: SprintUpdate) -> ApiSprint:
        """
        Update a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint to update
            sprint_update: Sprint update data
            
        Returns:
            Updated API Sprint model
        """
        # Convert dates if provided
        start_date = None
        if sprint_update.start_date:
            start_date = datetime.fromisoformat(sprint_update.start_date)
            
        end_date = None
        if sprint_update.end_date:
            end_date = datetime.fromisoformat(sprint_update.end_date)
        
        # Update the sprint using the sprint service
        sprint = await self.sprint_service.update_sprint(
            project_id=project_id,
            sprint_name=sprint_name,
            name=sprint_update.name,
            description=sprint_update.description,
            start_date=start_date,
            end_date=end_date,
            status=sprint_update.status
        )
        
        # Convert to API model
        pydantic_sprint = sprint_to_pydantic(sprint)
        api_sprint = ApiSprint.from_core_model(pydantic_sprint, project_id)
        
        return api_sprint
    
    async def delete_sprint(self, project_id: str, sprint_name: str) -> bool:
        """
        Delete a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint to delete
            
        Returns:
            True if deleted, False otherwise
        """
        return await self.sprint_service.delete_sprint(project_id, sprint_name)
    
    async def list_sprints(self, project_id: str, status_filter: Optional[str] = None) -> List[ApiSprint]:
        """
        List all sprints for a project.
        
        Args:
            project_id: ID of the project
            status_filter: Optional status to filter by
            
        Returns:
            List of API Sprint models
        """
        # Get sprints using the sprint service
        sprints = await self.sprint_service.list_sprints(project_id, status_filter)
        
        # Convert to API models
        api_sprints = []
        for sprint in sprints:
            pydantic_sprint = sprint_to_pydantic(sprint)
            api_sprint = ApiSprint.from_core_model(pydantic_sprint, project_id)
            api_sprints.append(api_sprint)
        
        return api_sprints
    
    async def start_sprint(self, project_id: str, sprint_name: str) -> ApiSprint:
        """
        Start a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            Updated API Sprint model
        """
        # Start the sprint using the sprint service
        sprint = await self.sprint_service.start_sprint(project_id, sprint_name)
        
        # Convert to API model
        pydantic_sprint = sprint_to_pydantic(sprint)
        api_sprint = ApiSprint.from_core_model(pydantic_sprint, project_id)
        
        return api_sprint
    
    async def complete_sprint(self, project_id: str, sprint_name: str) -> ApiSprint:
        """
        Complete a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            Updated API Sprint model
        """
        # Complete the sprint using the sprint service
        sprint = await self.sprint_service.complete_sprint(project_id, sprint_name)
        
        # Convert to API model
        pydantic_sprint = sprint_to_pydantic(sprint)
        api_sprint = ApiSprint.from_core_model(pydantic_sprint, project_id)
        
        return api_sprint
    
    async def get_sprint_progress(self, project_id: str, sprint_name: str) -> Dict[str, Any]:
        """
        Get progress statistics for a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            Dictionary with progress statistics
        """
        return await self.sprint_service.get_sprint_progress(project_id, sprint_name)
    
    async def get_sprint_todos(self, project_id: str, sprint_name: str, status_filter: Optional[str] = None) -> List[ApiTodoItem]:
        """
        Get all todo items for a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            status_filter: Optional status to filter by
            
        Returns:
            List of API TodoItem models
        """
        # Get todos using the sprint service
        todos = await self.sprint_service.get_sprint_todos(project_id, sprint_name, status_filter)
        
        # Convert to API models
        api_todos = []
        for todo in todos:
            pydantic_todo = todo_to_pydantic(todo)
            api_todo = ApiTodoItem.from_core_model(pydantic_todo, todo.id, sprint_name, project_id)
            api_todos.append(api_todo)
        
        return api_todos
    
    async def move_todo_to_sprint(self, project_id: str, todo_title: str, target_sprint_name: str) -> ApiTodoItem:
        """
        Move a todo item to a different sprint.
        
        Args:
            project_id: ID of the project
            todo_title: Title of the todo item
            target_sprint_name: Name of the target sprint
            
        Returns:
            Updated API TodoItem model
        """
        # Move the todo using the sprint service
        todo = await self.sprint_service.move_todo_to_sprint(project_id, todo_title, target_sprint_name)
        
        # Convert to API model
        pydantic_todo = todo_to_pydantic(todo)
        api_todo = ApiTodoItem.from_core_model(pydantic_todo, todo.id, target_sprint_name, project_id)
        
        return api_todo
    
    async def create_todo(self, project_id: str, todo_create: TodoItemCreate) -> ApiTodoItem:
        """Create a new todo item.
        
        Args:
            project_id: ID of the project to add the todo to
            todo_create: Todo creation data
            
        Returns:
            The created todo in API format
            
        Raises:
            ValueError: If the project does not exist or the specified sprint does not exist
        """
        # Add the todo to the project using the domain service
        await self.project_service.add_todo_to_project(
            project_id=project_id,
            title=todo_create.title,
            description=todo_create.description,
            status=todo_create.status,
            assigned_to=todo_create.assigned_to,
            priority=todo_create.priority,
            sprint_name=todo_create.sprint_name,
            tags=todo_create.tags
        )
        
        # Get the updated project
        domain_project = await self.project_service.get_project(project_id)
        
        # Find the created todo
        domain_todo = None
        
        if todo_create.sprint_name:
            # Find the sprint
            domain_sprint = next((s for s in domain_project.sprints if s.name == todo_create.sprint_name), None)
            
            if domain_sprint:
                # Find the todo in the sprint
                domain_todo = next((t for t in domain_sprint.todos if t.title == todo_create.title), None)
        else:
            # Find the todo in the project
            domain_todo = next((t for t in domain_project.todos if t.title == todo_create.title), None)
        
        if not domain_todo:
            raise ValueError(f"Failed to create todo {todo_create.title}")
        
        # Convert domain todo to API todo
        pydantic_todo = todo_to_pydantic(domain_todo)
        api_todo = ApiTodoItem.from_core_model(pydantic_todo, domain_todo.id, todo_create.sprint_name, project_id)
        
        return api_todo
    
    async def update_todo(self, project_id: str, todo_id: str, todo_update: TodoItemUpdate) -> ApiTodoItem:
        """Update a todo item.
        
        Args:
            project_id: ID of the project
            todo_id: ID of the todo to update
            todo_update: Todo update data
            
        Returns:
            The updated todo in API format
            
        Raises:
            ValueError: If the project or todo does not exist
        """
        # Get the existing project
        domain_project = await self.project_service.get_project(project_id)
        
        if not domain_project:
            raise ValueError(f"Project with ID {project_id} does not exist")
        
        # Find the todo to update
        domain_todo = None
        sprint_name = None
        
        # Check project todos
        for todo in domain_project.todos:
            if todo.id == todo_id:
                domain_todo = todo
                break
        
        # If not found in project todos, check sprint todos
        if not domain_todo:
            for sprint in domain_project.sprints:
                for todo in sprint.todos:
                    if todo.id == todo_id:
                        domain_todo = todo
                        sprint_name = sprint.name
                        break
                if domain_todo:
                    break
        
        if not domain_todo:
            raise ValueError(f"Todo with ID {todo_id} does not exist in project {domain_project.name}")
        
        # Update the todo fields
        if todo_update.title is not None:
            domain_todo.title = todo_update.title
        
        if todo_update.description is not None:
            domain_todo.description = todo_update.description
        
        if todo_update.status is not None:
            domain_todo.status = todo_update.status
            
            # Update completed_at if status is DONE
            if todo_update.status == "DONE":
                domain_todo.completed_at = datetime.now()
        
        if todo_update.assigned_to is not None:
            domain_todo.assigned_to = todo_update.assigned_to
        
        if todo_update.priority is not None:
            domain_todo.priority = todo_update.priority
        
        if todo_update.depends_on is not None:
            domain_todo.depends_on = todo_update.depends_on
        
        if todo_update.tags is not None:
            domain_todo.tags = todo_update.tags
        
        # Handle sprint assignment changes
        if todo_update.sprint_name is not None and todo_update.sprint_name != sprint_name:
            # Move todo to a different sprint or to project level
            
            # First remove from current location
            if sprint_name:
                # Remove from current sprint
                sprint = next((s for s in domain_project.sprints if s.name == sprint_name), None)
                if sprint:
                    sprint.todos = [t for t in sprint.todos if t.id != todo_id]
            else:
                # Remove from project todos
                domain_project.todos = [t for t in domain_project.todos if t.id != todo_id]
            
            # Then add to new location
            if todo_update.sprint_name:
                # Add to new sprint
                new_sprint = next((s for s in domain_project.sprints if s.name == todo_update.sprint_name), None)
                if new_sprint:
                    new_sprint.todos.append(domain_todo)
                else:
                    raise ValueError(f"Sprint {todo_update.sprint_name} does not exist in project {domain_project.name}")
            else:
                # Add to project todos
                domain_project.todos.append(domain_todo)
            
            # Update sprint_name for return value
            sprint_name = todo_update.sprint_name
        
        # Update the project using the domain service
        await self.project_service.update_project(domain_project)
        
        # Convert domain todo to API todo
        pydantic_todo = todo_to_pydantic(domain_todo)
        api_todo = ApiTodoItem.from_core_model(pydantic_todo, domain_todo.id, sprint_name, project_id)
        
        return api_todo

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
        
        # TODO: Implement actual chat with project agent
        # This is a placeholder implementation
        
        return ChatResponse(
            conversation_id=conversation_id,
            message="This is a placeholder response from the project agent.",
            project_id=None,
            status="completed"
        )

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
