"""
Chat Service

This module provides services for managing chat interactions with project agents.
It focuses solely on chat operations, delegating project management to ProjectService.
"""

from typing import Dict, Any, Optional

from roboco.services.project_service import ProjectService
from roboco.core.models.chat import ChatRequest, ChatResponse, ChatStatus
from roboco.utils.id_generator import generate_short_id

from loguru import logger

# Initialize logger immediately after import
logger = logger.bind(module=__name__)

class ChatService:
    """
    Service for chat interactions with project agents.
    
    This service focuses exclusively on orchestrating chat operations
    and delegates all project management to the ProjectService.
    """
    
    def __init__(self):
        """Initialize the chat service with its dependencies."""
        # Only need reference to the project service
        self.project_service = ProjectService()
    
    async def start_chat(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Start a new chat session, creating a project from the query.
        
        Args:
            chat_request: The chat request containing the query
            
        Returns:
            Response with project ID and results
        """
        try:
            # Let project service handle creating the project with appropriate ID
            project = await self.project_service.initiate_project(
                query=chat_request.query,
                teams=["versatile"],  # Default to versatile team
                metadata={"chat_request": chat_request.dict()}
            )
            
            if not project:
                raise ValueError("Failed to create project - project_service.initiate_project returned None")
                
            # Log the project details to help diagnose issues
            logger.info(f"Created project with ID: {project.project_id}, name: {project.name}")
            
            # Pass the project instance directly to execute_project
            logger.info(f"Executing tasks for project: {project.project_id}")
            try:
                await self.project_service.execute_project(project)
            except Exception as exec_err:
                logger.error(f"Error executing project: {str(exec_err)}")
                # Continue with partial results, don't abort the whole operation
            
            # Get project status from project service
            try:
                project_status = await self.project_service.get_project_status(project.project_id)
            except Exception as status_err:
                logger.error(f"Error getting project status: {str(status_err)}")
                project_status = {"status": "error", "message": str(status_err)}
            
            # Create response from project data
            return ChatResponse(
                project_id=project.project_id,
                message=f"Project '{project.name}' created and executed successfully",
                project_details=project_status,
                status=ChatStatus.COMPLETED
            )
        except Exception as e:
            import traceback
            logger.error(f"Error in start_chat: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Return error response
            return ChatResponse(
                project_id=generate_short_id(),  # Generate placeholder ID for error case
                message=f"Error: {str(e)}",
                status=ChatStatus.FAILED
            )
    
    async def continue_project_chat(self, project_id: str, query: str) -> ChatResponse:
        """
        Continue a chat about a specific existing project.
        
        Args:
            project_id: ID of the project to discuss
            query: User's query about the project
            
        Returns:
            Response with project ID and results
        """
        try:
            # Get the project to verify it exists
            project = await self.project_service.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
                
            # Use initiate_project with existing project ID
            response_data = await self.project_service.initiate_project(
                query=query,
                project_id=project_id,
                teams=["planning"],  # Default to planning team
                metadata={"context_type": "project_query"}
            )
            
            # Get the updated project status
            project_status = await self.project_service.get_project_status(project_id)
            
            # Format a user-friendly response message
            message = f"Query about project '{project.name}': {query}\n\n"
            if hasattr(response_data, 'name'):
                message += f"Response: Analysis completed for {response_data.name}"
            else:
                message += "Response: Analysis completed"
                
            # Return response
            return ChatResponse(
                project_id=project_id,
                message=message,
                project_details=project_status,
                status=ChatStatus.COMPLETED
            )
                
        except Exception as e:
            logger.error(f"Error in continue_project_chat: {str(e)}")
            # Return error response
            return ChatResponse(
                project_id=project_id,
                message=f"Error: {str(e)}",
                status=ChatStatus.FAILED
            )

    async def get_project(self, project_id: str) -> Any:
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            Project object if found, None otherwise
        """
        return await self.project_service.get_project(project_id)
