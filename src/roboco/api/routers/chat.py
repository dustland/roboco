"""
Chat Router

This module defines the FastAPI router for chat-related endpoints.
It follows the DDD principles by using the domain services through the API service.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from roboco.services.api_service import ApiService
from roboco.api.schemas.chat import ChatRequest, ChatResponse
from roboco.infrastructure.repositories.file_project_repository import FileProjectRepository
from roboco.services.project_service import ProjectService


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


# Dependency to get the API service
async def get_api_service():
    """Get the API service instance."""
    # Create the repository
    repository = FileProjectRepository()
    
    # Create the domain service
    project_service = ProjectService(repository)
    
    # Create the API service
    api_service = ApiService(project_service)
    
    return api_service


@router.post("/", response_model=ChatResponse)
async def chat_with_project_agent(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Chat with the project agent to create or update a project.
    
    Parameters:
    - query: Natural language query to process
    - teams: Optional specific teams to assign
    - conversation_id: Optional ID to continue existing conversation
    
    Returns the chat response with project details if created.
    """
    try:
        result = await api_service.chat_with_project_agent(
            chat_request.query,
            chat_request.teams,
            chat_request.conversation_id,
            background_tasks
        )
        
        # Create a conversation ID if one wasn't provided
        conversation_id = chat_request.conversation_id or result.get("conversation_id", "")
        
        return ChatResponse.from_chat_result(result, conversation_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.get("/{conversation_id}", response_model=ChatResponse)
async def get_chat_status(
    conversation_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Get the status of a chat conversation.
    
    Parameters:
    - conversation_id: ID of the conversation
    
    Returns the chat response with current status.
    """
    try:
        result = await api_service.get_chat_status(conversation_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Conversation with ID {conversation_id} not found")
        
        return ChatResponse.from_chat_result(result, conversation_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat status: {str(e)}")
