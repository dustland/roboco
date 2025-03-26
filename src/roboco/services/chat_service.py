"""
Chat Service

This module provides services for managing chat interactions with project agents.
It follows DDD principles by encapsulating chat-related business logic.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import os
from roboco.core.logger import get_logger

logger = get_logger(__name__)

from roboco.core.project_fs import ProjectFS
from roboco.core.config import load_config, get_llm_config, get_workspace
from roboco.teams.planning import PlanningTeam
from roboco.core.project_executor import ProjectExecutor
from roboco.services.project_service import ProjectService
from roboco.core.models.chat import ChatRequest, ChatResponse


class ChatService:
    """
    Service for managing chat interactions with project agents.
    
    This service follows the DDD principles by encapsulating chat-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self):
        """
        Initialize the chat service with its dependencies.
        """
        # Store conversation history - in a real implementation, this would be persisted
        self.conversations = {}
        
        # Load config for LLM settings
        self.config = load_config()
        self.llm_config = get_llm_config(self.config)
        
        # Set workspace directory from configuration
        self.workspace_dir = str(get_workspace(self.config))
        
        # Create services - reuse instances instead of creating new ones per request
        self.project_service = ProjectService()
    
    async def start_chat(self, chat_request):
        """
        Process a chat request with the project agent.
        
        Args:
            chat_request: The chat request containing query and other parameters
            
        Returns:
            ChatResponse object with response details
        """
        # Create or get conversation ID
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation if it doesn't exist
        conversation = self.conversations.get(conversation_id)
        if not conversation:
            conversation = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "project_id": None
            }
            self.conversations[conversation_id] = conversation
        
        # Add user message to conversation history
        conversation["messages"].append({
            "role": "user",
            "content": chat_request.query,
            "timestamp": datetime.now().isoformat()
        })
        
        # First message = create project, subsequent messages = chat
        if len(conversation["messages"]) == 1:
            response = await self._create_and_execute_project(conversation_id, chat_request)
        else:
            response = await self._handle_follow_up_message(conversation_id, chat_request)
        
        return response
    
    async def _handle_follow_up_message(self, conversation_id: str, chat_request):
        """Handle a follow-up message in an existing conversation."""
        from roboco.core.models.chat import ChatResponse
        
        conversation = self.conversations[conversation_id]
        project_id = conversation.get("project_id")
        
        # Create planner for general chat
        planning_team = PlanningTeam(workspace_dir=self.workspace_dir)
        
        # Get project status if available
        project_status = None
        response_message = ""
        
        if project_id:
            project_status = await self.project_service.get_project_status(project_id)
            
            # Add project context to the query
            context = (
                f"Project: {project_status['name']}\n"
                f"Status: {project_status['status']}\n"
                f"Progress: {project_status['progress']}% "
                f"({project_status['completed_tasks']}/{project_status['total_tasks']} tasks completed)\n\n"
            )
            
            # Add project context to query
            contextual_query = (
                f"The user is asking about project '{project_status['name']}' "
                f"which is {project_status['progress']}% complete. "
                f"Their query is: {chat_request.query}"
            )
            
            # Run chat with context
            chat_result = await planning_team.run_chat(
                query=contextual_query,
                teams=chat_request.teams
            )
            
            # Combine status and response
            response_message = context + chat_result["response"]
        else:
            # No project context, just regular chat
            chat_result = await planning_team.run_chat(
                query=chat_request.query,
                teams=chat_request.teams
            )
            response_message = chat_result["response"]
        
        # Add response to conversation history
        conversation["messages"].append({
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Return formatted response
        return ChatResponse(
            conversation_id=conversation_id,
            message=response_message,
            project_id=project_id,
            project_details=project_status,
            status="completed"
        )
    
    async def _create_and_execute_project(
        self,
        conversation_id: str,
        chat_request: ChatRequest
    ) -> ChatResponse:
        """
        Create and execute a project based on the chat request.
        
        Args:
            conversation_id: ID of the conversation
            chat_request: The chat request containing the query
            
        Returns:
            ChatResponse with the results
        """
        logger.info(f"Creating project from query: {chat_request.query}")
        
        # Create project from query
        project = await self.project_service.create_project_from_query(
            chat_request.query
        )
        
        logger.info(f"Initializing project executor for project: {project.directory}")
        # Initialize project executor
        executor = ProjectExecutor(project.directory)
        
        # Execute the project
        results = await executor.execute_project()
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=f"Project {project.name} created and executed successfully",
            status="completed",
            project_id=project.id,
            project_details={"directory": project.directory}
        )
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the history of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary with conversation details if found, None otherwise
        """
        return self.conversations.get(conversation_id)
