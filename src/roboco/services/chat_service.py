"""
Chat Service

This module provides services for managing chat interactions with project agents.
It follows DDD principles by encapsulating chat-related business logic.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio
from loguru import logger
import os

from roboco.domain.models.project import Project
from roboco.domain.repositories.project_repository import ProjectRepository
from roboco.api.schemas.chat import ChatRequest, ChatResponse
from roboco.core.config import load_config, get_llm_config
from roboco.teams.project_team import ProjectTeam


class ChatService:
    """
    Service for managing chat interactions with project agents.
    
    This service follows the DDD principles by encapsulating chat-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize the chat service with its dependencies.
        
        Args:
            project_repository: Repository for project data access
        """
        self.project_repository = project_repository
        # Store conversation history - in a real implementation, this would be persisted
        self.conversations = {}
        
        # Load config for LLM settings
        self.config = load_config()
        self.llm_config = get_llm_config(self.config)
        
        # Set workspace directory
        self.workspace_dir = os.path.expanduser("~/roboco_workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    async def chat_with_project_agent(self, chat_request: ChatRequest) -> ChatResponse:
        """
        Process a chat request with the project agent.
        
        Args:
            chat_request: The chat request containing query and other parameters
            
        Returns:
            ChatResponse object with response details
        """
        # Create a new conversation ID if not provided
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "project_id": None
            }
        
        # Add user message to conversation history
        self.conversations[conversation_id]["messages"].append({
            "role": "user",
            "content": chat_request.query,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # Create a new project team for this conversation
            project_team = ProjectTeam(
                llm_config=self.llm_config,
                workspace_dir=self.workspace_dir
            )
            
            # Run the chat session
            chat_result = await project_team.run_chat(
                query=chat_request.query,
                teams=chat_request.teams
            )
            
            # Extract the response
            response_message = chat_result["response"]
            
            # Check if a project was created during the conversation
            project_id = None
            project_details = None
            
            # Extract project ID from the response if available
            # This is a simplified approach - in a real implementation, we would
            # parse the response more robustly or track project creation directly
            if "project has been created" in response_message.lower():
                # Get the most recently created project
                projects = self.project_repository.list_projects()
                if projects:
                    latest_project = projects[-1]
                    project_id = latest_project.id
                    project_details = {
                        "name": latest_project.name,
                        "description": latest_project.description,
                        "teams": latest_project.teams
                    }
                    
                    # Update conversation with project ID
                    self.conversations[conversation_id]["project_id"] = project_id
            
            # Add agent response to conversation history
            self.conversations[conversation_id]["messages"].append({
                "role": "assistant",
                "content": response_message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Return a properly formatted ChatResponse
            return ChatResponse(
                conversation_id=conversation_id,
                message=response_message,
                project_id=project_id,
                project_details=project_details,
                status="completed"
            )
            
        except Exception as e:
            logger.error(f"Error in chat with project agent: {str(e)}")
            error_message = f"An error occurred while processing your request: {str(e)}"
            
            # Add error to conversation history
            self.conversations[conversation_id]["messages"].append({
                "role": "assistant",
                "content": error_message,
                "timestamp": datetime.now().isoformat()
            })
            
            return ChatResponse(
                conversation_id=conversation_id,
                message=error_message,
                project_id=None,
                status="error"
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
