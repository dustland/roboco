"""
Chat router.

This module defines the FastAPI routes for chat-related operations.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from roboco.api.models.chat import ChatRequest as ApiChatRequest, ChatResponse as ApiChatResponse
from roboco.core.models.chat import ChatRequest as ServiceChatRequest, ChatResponse as ServiceChatResponse
from roboco.api.dependencies import get_api_service

router = APIRouter(
    tags=["chat"]
)

def api_to_service_request(api_request: ApiChatRequest) -> ServiceChatRequest:
    """Convert an API chat request to a service chat request."""
    return ServiceChatRequest(
        query=api_request.query,
        task_id=api_request.task_id
    )

def service_to_api_response(service_response: ServiceChatResponse) -> ApiChatResponse:
    """Convert a service chat response to an API chat response."""
    return ApiChatResponse(
        conversation_id=service_response.conversation_id,
        message=service_response.message,
        project_id=service_response.project_id,
        task_id=service_response.task_id,
        status=service_response.status
    )

@router.post("/", response_model=ApiChatResponse)
async def start_chat(
    request: ApiChatRequest,
    api_service: Any = Depends(get_api_service)
):
    """Start a new chat session."""
    try:
        # Convert API request to service request
        service_request = api_to_service_request(request)
        
        # Call service method
        service_response = await api_service.chat_service.start_chat(service_request)
        
        # Convert service response to API response
        return service_to_api_response(service_response)
    except Exception as e:
        logger.error(f"Error starting chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting chat: {str(e)}"
        )

@router.post("/project/{project_id}", response_model=ApiChatResponse)
async def chat_with_project(
    project_id: str,
    request: ApiChatRequest,
    api_service: Any = Depends(get_api_service)
):
    """Chat about a specific project."""
    try:
        # Convert API request to service request
        service_request = api_to_service_request(request)
        
        # Call service method
        service_response = await api_service.chat_service.continue_project_chat(
            project_id=project_id,
            query=service_request.query
        )
        
        # Convert service response to API response
        return service_to_api_response(service_response)
    except Exception as e:
        logger.error(f"Error chatting with project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error chatting with project: {str(e)}"
        ) 