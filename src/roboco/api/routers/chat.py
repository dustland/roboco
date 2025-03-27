"""
Chat Router

This module defines the FastAPI router for chat-related endpoints.
It follows the DDD principles by using the domain services through the API service.
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime

from roboco.api.dependencies import get_api_service
from roboco.core.models.chat import ChatRequest, ChatResponse


router = APIRouter(
    tags=["chat"],
)


@router.post("/", response_model=ChatResponse)
async def start_chat(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    api_service = Depends(get_api_service)
):
    """
    Start a new chat or continue an existing conversation.
    
    For the first message in a conversation, this will:
    1. Plan a project by generating tasks.md file
    2. Execute all tasks in the tasks.md file using the VersatileTeam
    
    For subsequent messages, it will continue the conversation with the project agent.
    
    Parameters:
    - query: Natural language query to process
    - teams: Optional specific teams to assign
    - conversation_id: Optional ID to continue existing conversation
    
    Returns the chat response with project details if created.
    """
    try:
        result = await api_service.start_chat(chat_request)
        
        # Create a conversation ID if one wasn't provided
        conversation_id = chat_request.conversation_id or result.conversation_id
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.get("/{conversation_id}", response_model=ChatResponse)
async def get_chat_status(
    conversation_id: str,
    api_service = Depends(get_api_service)
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


@router.post("/{conversation_id}/execute", response_model=ChatResponse)
async def execute_project(
    conversation_id: str,
    api_service = Depends(get_api_service)
):
    """
    Execute or re-execute the project associated with a conversation.
    
    This endpoint allows you to execute a project that was previously planned
    but may have failed to execute properly.
    
    Parameters:
    - conversation_id: ID of the conversation with a project
    
    Returns the chat response with execution results.
    """
    try:
        # Check if conversation exists
        conversation = await api_service.chat_service.get_conversation_history(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation with ID {conversation_id} not found")
        
        # Check if conversation has a project
        project_id = conversation.get("project_id")
        if not project_id:
            raise HTTPException(status_code=400, detail="No project associated with this conversation")
        
        # Get the project
        project = await api_service.project_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
        
        # Re-execute the project
        executor = await api_service.chat_service._get_project_executor(project.directory)
        execution_result = await executor.execute_project()
        
        # Prepare response message
        if execution_result.get("error"):
            response_message = f"I've encountered an error during execution: {execution_result.get('error')}"
            status = "error"
        else:
            response_message = "I've successfully executed your project:\n\n"
            
            # Add task results to the response
            if "tasks" in execution_result:
                for task_name, task_result in execution_result.get("tasks", {}).items():
                    task_status = task_result.get("status", "unknown")
                    if task_status == "completed" or task_status == "already_completed":
                        response_message += f"- ✅ {task_name}\n"
                    else:
                        response_message += f"- ❌ {task_name}: {task_result.get('error', 'Failed')}\n"
            
            response_message += f"\nYou can find all project files in: {project.directory}"
            status = "completed"
        
        # Add response to conversation history
        conversation["messages"].append({
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=response_message,
            project_id=project_id,
            project_details={
                "name": project.name,
                "description": project.description,
                "directory": project.directory,
                "teams": project.teams
            },
            status=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing project: {str(e)}")
