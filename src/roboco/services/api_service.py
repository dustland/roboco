"""
API Service

This module provides services for the API layer, orchestrating interactions between
the API endpoints and the domain services.
"""

from typing import List, Optional, Dict, Any
import os


from roboco.services.project_service import ProjectService
from roboco.services.agent_service import AgentService
from roboco.services.chat_service import ChatService
from roboco.core.models.task import Task
from roboco.core.models.project import Project
from roboco.core.models.chat import ChatRequest, ChatResponse
from roboco.core.task_manager import TaskManager
from roboco.core.config import load_config

from loguru import logger

# Initialize logger immediately after import
logger = logger.bind(module=__name__)

# Local utility function
def project_to_pydantic(project):
    """Convert domain project to Pydantic model."""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }

class ApiService:
    """Service for API operations.
    
    This service acts as a facade for the API layer, orchestrating interactions
    between the API endpoints and the domain services.
    
    It follows the Dependency Injection pattern, accepting service dependencies
    through the constructor rather than creating them directly.
    
    This class is implemented as a singleton to ensure consistent service access.
    """
    
    # Class variable for singleton instance
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance.
        
        Returns:
            ApiService: The singleton instance
        """
        if cls._instance is None:
            # Import here to avoid circular imports
            from roboco.services.project_service import ProjectService
            from roboco.services.agent_service import AgentService
            
            # Create the project service
            project_service = ProjectService()
            
            # Create the agent service
            agent_service = AgentService()
            
            # Create new instance
            cls._instance = cls(
                project_service=project_service,
                agent_service=agent_service,
                # chat_service will be created in __init__
            )
        
        return cls._instance
    
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
        
        # Lazy import to avoid circular imports
        from roboco.services.chat_service import ChatService
        
        # Create services with default implementations if not provided
        self.chat_service = chat_service or ChatService()
        
        # Let the ProjectFS/FileSystem handle workspace paths
        self.workspace_dir = ""
        config = load_config()
        os.makedirs(os.path.join(config.workspace_root, self.workspace_dir), exist_ok=True)

    async def list_projects(self, project_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List projects, optionally filtered by project ID.
        
        Args:
            project_id: Optional project ID to filter by
            limit: Maximum number of projects to return
            
        Returns:
            List of project summary data
        """
        try:
            return await self.chat_service.list_projects(project_id, limit)
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            return []
    
    async def get_project(self, project_id: str) -> Optional[Project]:
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
        api_project = Project.from_dict(pydantic_project)
        
        return api_project
    
    async def create_project(self, project_data: Dict[str, Any]) -> Project:
        """Create a new project.
        
        Args:
            project_data: Dictionary with project creation data:
                - name: Name of the project (required)
                - description: Description of the project
            
        Returns:
            The created project in API format
        """
        # Create a Project instance using the create class method
        project_instance = Project.create(**project_data)
        
        # Create the project using the domain service
        domain_project = await self.project_service.create_project(
            name=project_instance.name,
            description=project_instance.description
        )
        
        # Convert domain project to API project
        pydantic_project = project_to_pydantic(domain_project)
        api_project = Project.from_dict(pydantic_project)
        
        return api_project
    
    async def update_project(self, project_id: str, project_data: Dict[str, Any]) -> Project:
        """Update a project.
        
        Args:
            project_id: ID of the project to update
            project_data: Dictionary with fields to update:
                - name: Optional new name for the project
                - description: Optional new description for the project
            
        Returns:
            The updated project in API format
            
        Raises:
            ValueError: If the project does not exist
        """
        # Get the existing project
        domain_project = await self.project_service.get_project(project_id)
        
        if not domain_project:
            raise ValueError(f"Project with ID {project_id} does not exist")
        
        # Update the project fields using the update method
        project_update = Project.update_from_dict(project_id, project_data)
        
        # Apply updates to domain project
        if project_update.name is not None:
            domain_project.name = project_update.name
        
        if project_update.description is not None:
            domain_project.description = project_update.description
        
        # Update the project using the domain service
        await self.project_service.update_project(domain_project)
        
        # Get the updated project
        updated_domain_project = await self.project_service.get_project(project_id)
        
        # Convert domain project to API project
        pydantic_project = project_to_pydantic(updated_domain_project)
        api_project = Project.from_dict(pydantic_project)
        
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
    
    async def list_tasks(self, project_id: str) -> List[Task]:
        """List all tasks for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of all tasks for the project in API format
            
        Raises:
            ValueError: If the project does not exist
        """
        # Get the project
        project = await self.project_service.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
            
        # Load tasks from the project
        project.load_tasks()
        
        # Convert domain tasks to API tasks (handle both dict and Task objects)
        api_tasks = []
        for task in project.tasks:
            if isinstance(task, dict):
                api_tasks.append(Task(**task))
            elif isinstance(task, Task):
                api_tasks.append(task)
            else:
                # Try to convert to dict then to Task
                task_dict = task.dict() if hasattr(task, 'dict') else vars(task)
                api_tasks.append(Task(**task_dict))
        
        return api_tasks
    
    async def get_task(self, project_id: str, task_id: str) -> Optional[Task]:
        """Get a task by its ID.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to retrieve
            
        Returns:
            The task in API format if found, None otherwise
            
        Raises:
            ValueError: If the project does not exist
        """
        # Get the project
        project = await self.project_service.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
            
        # Load tasks from the project
        project.load_tasks()
        
        # Find the task with the matching ID
        task = next((t for t in project.tasks if t.id == task_id), None)
        
        if not task:
            return None
            
        # Convert to API task if it's not already
        if not isinstance(task, Task):
            task = Task(**task)
            
        return task
    
    async def start_chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Process a chat request with the project agent.
        
        Args:
            chat_request: The chat request containing the query and other parameters
            
        Returns:
            ChatResponse object with the response details
        """
        return await self.chat_service.start_chat(chat_request)
    
    async def get_project_status(self, project_id: str, include_history: bool = False) -> Optional[Dict[str, Any]]:
        """Get the status of a project conversation.
        
        Args:
            project_id: ID of the project
            include_history: Whether to include message history or task metadata in the response
            
        Returns:
            Dictionary with project details or None if not found
        """
        # Get project status using the enhanced ChatService method
        project_status = await self.chat_service.get_project_status(project_id)
        
        if not project_status:
            # If no status record exists, try to get basic project history
            project_history = await self.chat_service.get_project_history(project_id)
            
            if not project_history:
                logger.warning(f"Project {project_id} not found")
                return None
                
            # If we have history but no status, return basic info from the history
            return {
                "project_id": project_history.project_id,
                "title": project_history.title,
                "message": project_history.messages[-1].content if project_history.messages else "",
                "status": project_history.status,
                "created_at": project_history.created_at,
                "updated_at": project_history.updated_at,
                "messages": [msg.dict() for msg in project_history.messages] if include_history else None,
                "files": project_history.files or []
            }
        
        # Get the full result as a dictionary
        status_dict = project_status.dict()
        
        # Include message history if requested
        if include_history:
            if not status_dict.get("messages"):
                project_history = await self.chat_service.get_project_history(project_id)
                if project_history:
                    status_dict["messages"] = [msg.dict() for msg in project_history.messages]
            
            # Include task metadata if no messages were included
            if not status_dict.get("messages") and not status_dict.get("tasks"):
                # Get the project
                project = await self.project_service.get_project(project_id)
                if project:
                    # Load tasks from the project
                    project.load_tasks()
                    
                    # Add task metadata to result
                    status_dict["tasks"] = [
                        {
                            "id": task.id,
                            "name": task.name,
                            "status": task.status,
                            "created_at": task.created_at,
                            "updated_at": task.updated_at
                        } for task in project.tasks
                    ]
        
        return status_dict
    
    async def get_task_json(self, project_id: str) -> Dict[str, Any]:
        """Get the tasks for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with task content and metadata
        """
        # Get the project
        project = await self.project_service.get_project(project_id)
        
        # Create a filesystem for the project
        from roboco.core.fs import ProjectFS
        fs = ProjectFS(project_id=project_id)
        
        # Create a task manager for task operations
        task_manager = TaskManager(fs=fs)
        
        # Load tasks directly from database
        from roboco.db.service import get_tasks_by_project
        tasks = get_tasks_by_project(project_id)
        
        # Convert tasks to a dictionary structure for API response
        tasks_data = {
            "project_id": project_id,
            "tasks": [task.to_dict() for task in tasks]
        }
        
        # Generate tasks.md content from tasks
        tasks_md = task_manager.tasks_to_markdown(tasks, project.name)
        
        # Always update the tasks.md file to ensure it's in sync with the database
        project.fs.write_sync("tasks.md", tasks_md)
        
        return {
            "content": tasks_md,
            "data": tasks_data,
            "project_id": project_id,
            "updated_at": project.updated_at
        }

    async def stop_chat(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Stop a running chat.
        
        Args:
            project_id: ID of the project/chat to stop
            
        Returns:
            Updated chat status or None if not found
        """
        try:
            return await self.chat_service.stop_project(project_id)
        except Exception as e:
            logger.error(f"Error stopping chat for project {project_id}: {str(e)}")
            return None

    async def get_messages(self, project_id: Optional[str] = None, task_id: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get messages filtered by project ID and/or task ID with pagination.
        
        Args:
            project_id: Optional ID of the project to filter by
            task_id: Optional ID of the task to filter by
            limit: Maximum number of messages to return
            offset: Offset for pagination
            
        Returns:
            List of messages with agent information
        """
        from roboco.db.service import get_messages_by_task
        
        try:
            # If task_id is provided, filter by task
            if task_id:
                messages = get_messages_by_task(task_id)
                
                # Apply pagination
                paginated_messages = messages[offset:offset + limit]
                
                # Convert messages to dictionaries
                return [message.to_dict() for message in paginated_messages]
            # If only project_id is provided, we need to get all tasks for the project
            elif project_id:
                # Get the project to access its tasks
                project = await self.project_service.get_project(project_id)
                if not project:
                    logger.warning(f"Project {project_id} not found")
                    return []
                
                # Load tasks from the project
                project.load_tasks()
                
                # Collect messages from all tasks in the project
                all_messages = []
                for task in project.tasks:
                    task_messages = get_messages_by_task(task.id)
                    all_messages.extend(task_messages)
                
                # Sort messages by timestamp (assuming there's a timestamp field)
                all_messages.sort(key=lambda msg: msg.created_at if hasattr(msg, 'created_at') else 0)
                
                # Apply pagination
                paginated_messages = all_messages[offset:offset + limit]
                
                # Convert messages to dictionaries
                return [message.to_dict() for message in paginated_messages]
            # If neither is provided, return empty list
            else:
                logger.warning("No project_id or task_id provided for get_messages")
                return []
        except Exception as e:
            logger.error(f"Error getting messages (project_id={project_id}, task_id={task_id}): {str(e)}")
            return []
