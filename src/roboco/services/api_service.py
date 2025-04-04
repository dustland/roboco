"""
API Service

This module provides services for the API layer, orchestrating interactions between
the API endpoints and the domain services.
"""

from typing import List, Optional, Dict, Any
import os
from loguru import logger

logger = logger.bind(module=__name__)

from roboco.services.project_service import ProjectService
from roboco.services.agent_service import AgentService
from roboco.services.chat_service import ChatService
from roboco.core.models.task import Task
from roboco.core.models.project import Project
from roboco.core.models.chat import ChatRequest, ChatResponse
from roboco.core.config import load_config

# Local utility function
def project_to_pydantic(project):
    """Convert domain project to Pydantic model."""
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "directory": project.id,  # Always use project ID as directory
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

    async def list_projects(self) -> List[Project]:
        """List all projects.
        
        Returns:
            List of all projects in API format
        """
        domain_projects = await self.project_service.list_projects()
        
        # Convert domain projects to API projects
        api_projects = []
        for project in domain_projects:
            # Convert to Pydantic model
            pydantic_project = project_to_pydantic(project)
            
            # Create Project instance
            api_project = Project.from_dict(pydantic_project)
            api_projects.append(api_project)
        
        return api_projects
    
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
    
    async def create_project(self, project_create: ProjectCreate) -> Project:
        """Create a new project.
        
        Args:
            project_create: Project creation data
            
        Returns:
            The created project in API format
        """
        # Create the project using the domain service
        domain_project = await self.project_service.create_project(
            name=project_create.name,
            description=project_create.description,
            directory=project_create.directory,
            teams=project_create.teams,
            tags=project_create.tags
        )
        
        # Convert domain project to API project
        pydantic_project = project_to_pydantic(domain_project)
        api_project = Project.from_dict(pydantic_project)
        
        return api_project
    
    async def update_project(self, project_id: str, project_update: ProjectUpdate) -> Project:
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
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get the full chat history for a conversation with complete details.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary with conversation details and messages, or None if not found
        """
        history = await self.chat_service.get_conversation_history(conversation_id)
        
        if not history:
            logger.warning(f"Conversation {conversation_id} not found")
            return None
        
        # Return the history as a dictionary
        return history.dict()
        
    async def get_chat_status(self, conversation_id: str, include_history: bool = False) -> Optional[Dict[str, Any]]:
        """Get the status of a chat conversation.
        
        Args:
            conversation_id: ID of the conversation
            include_history: Whether to include message history in the response
            
        Returns:
            Dictionary with conversation details or None if not found
        """
        # Get conversation status using the enhanced ChatService method
        conversation_status = await self.chat_service.get_conversation_status(conversation_id)
        
        if not conversation_status:
            # If no status record exists, try to get basic conversation history
            conversation = await self.chat_service.get_conversation_history(conversation_id)
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
                
            # If we have history but no status, return basic info from the history
            return {
                "conversation_id": conversation.conversation_id,
                "project_id": conversation.project_id,
                "title": conversation.title,
                "message": conversation.messages[-1].content if conversation.messages else "",
                "status": conversation.status,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "messages": [msg.dict() for msg in conversation.messages] if include_history else None,
                "files": conversation.files or []
            }
        
        # Get the full result as a dictionary
        status_dict = conversation_status.dict()
        
        # Include message history if requested
        if include_history and not status_dict.get("messages"):
            conversation = await self.chat_service.get_conversation_history(conversation_id)
            if conversation:
                status_dict["messages"] = [msg.dict() for msg in conversation.messages]
        
        return status_dict
    
    async def create_task(self, project_id: str, task_create: TaskCreate) -> Optional[Task]:
        """Create a new task for a project.
        
        Args:
            project_id: ID of the project
            task_create: Task creation data
            
        Returns:
            The created task in API format
            
        Raises:
            ValueError: If the project does not exist
        """
        # Get the project
        project = await self.project_service.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
            
        # Convert task_create to a Task
        task = task_create.to_task(project_id=project_id)
        
        # Add the task to the project
        project.tasks.append(task)
        
        # Save the project
        project.save()
        
        return task
    
    async def update_task(self, project_id: str, task_id: str, task_update: TaskUpdate) -> Optional[Task]:
        """Update a task in a project.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to update
            task_update: Task update data
            
        Returns:
            The updated task in API format
            
        Raises:
            ValueError: If the project or task does not exist
        """
        # Get the project
        project = await self.project_service.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
            
        # Load tasks from the project
        project.load_tasks()
        
        # Find the task with the matching ID
        task_index = next((i for i, t in enumerate(project.tasks) if t.id == task_id), None)
        
        if task_index is None:
            return None
            
        # Get the existing task
        task = project.tasks[task_index]
        
        # Convert to Task object if it's not already
        if not isinstance(task, Task):
            task = Task(**task)
        
        # Apply updates to the task
        updated_task = task_update.apply_to_task(task)
        
        # Update the task in the project
        project.tasks[task_index] = updated_task
        
        # Save the project
        project.save()
        
        return updated_task
    
    async def get_task_markdown(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the task.md content for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Dictionary with the markdown content and metadata
            
        Raises:
            ValueError: If the project does not exist
        """
        # Get the project
        project = await self.project_service.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        try:
            # Try to read tasks.md file
            tasks_md = project.fs.read_sync("tasks.md")
            
            return {
                "content": tasks_md,
                "project_id": project_id,
                "updated_at": project.updated_at
            }
        except FileNotFoundError:
            # Create empty tasks.md if it doesn't exist
            empty_content = "# Tasks\n\nNo tasks defined yet.\n"
            project.fs.write_sync("tasks.md", empty_content)
            
            return {
                "content": empty_content,
                "project_id": project_id,
                "updated_at": project.updated_at
            }
        except Exception as e:
            logger.error(f"Error reading tasks.md for project {project_id}: {str(e)}")
            return None

    # Conversation-related methods
    
    async def list_conversations(self, project_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List conversations, optionally filtered by project ID.
        
        Args:
            project_id: Optional project ID to filter by
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation summary data
        """
        try:
            return await self.chat_service.list_conversations(project_id, limit)
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            return []
    
    async def list_messages_by_task(self, task_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """List messages associated with a specific task.
        
        Args:
            task_id: ID of the task
            limit: Maximum number of messages to return
            
        Returns:
            List of message summary data
        """
        try:
            # This would be implemented using a database query in a real implementation
            # Here we'll just return an empty list for demonstration purposes
            # The real implementation would search through conversation messages for those
            # with a matching task_id
            return []
            
            # Example real implementation:
            # Use a database query to find all messages with matching task_id
            # return await self.chat_service.find_messages_by_task_id(task_id, limit)
        except Exception as e:
            logger.error(f"Error listing messages for task {task_id}: {str(e)}")
            return []
    
    async def stop_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Stop a running conversation.
        
        Args:
            conversation_id: ID of the conversation to stop
            
        Returns:
            Updated conversation status or None if not found
        """
        try:
            return await self.chat_service.stop_conversation(conversation_id)
        except Exception as e:
            logger.error(f"Error stopping conversation {conversation_id}: {str(e)}")
            return None

    async def get_messages_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """Get all messages generated during execution of a specific task.
        
        Args:
            task_id: ID of the task
            
        Returns:
            List of messages with agent information
        """
        from roboco.db.service import get_messages_by_task
        
        try:
            # Get messages from the database
            messages = get_messages_by_task(task_id)
            
            # Convert messages to dictionaries
            return [message.to_dict() for message in messages]
        except Exception as e:
            logger.error(f"Error getting messages for task {task_id}: {str(e)}")
            return []
