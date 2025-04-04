"""
Task router.

This module defines the FastAPI routes for task-related operations.
It uses the simplified models and database service.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from roboco.core.models import (
    Task, Message
)
from roboco.api.models import (
    TaskUpdate, MessageCreate
)
from roboco.api.models.chat import (
    ChatRequest, ChatResponse
)
from roboco.api.dependencies import get_api_service
from roboco.db import service
from loguru import logger

from roboco.services.api_service import ApiService

router = APIRouter(
    tags=["tasks"]
)

@router.get("/{task_id}", response_model=Task)
def get_task(task_id: str):
    """Get a task by ID."""
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/{task_id}", response_model=Task)
def update_task(task_id: str, task_data: TaskUpdate):
    """Update a task."""
    task = service.update_task(task_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}")
def delete_task(task_id: str):
    """Delete a task."""
    success = service.delete_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

# Message routes scoped to a task
@router.post("/{task_id}/messages", response_model=Message)
def create_message(task_id: str, message_data: MessageCreate):
    """Create a new message in a task."""
    message = service.create_message(task_id, message_data)
    if not message:
        raise HTTPException(status_code=404, detail="Task not found")
    return message

@router.get("/{task_id}/messages", response_model=List[Dict[str, Any]])
async def get_task_messages(
    task_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """Get all messages generated during execution of a specific task."""
    try:
        messages = await api_service.get_messages_for_task(task_id)
        return messages
    except Exception as e:
        logger.error(f"Error getting messages for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages for task: {str(e)}"
        )

@router.get("/{task_id}/messages/{message_id}", response_model=Message)
def get_task_message(task_id: str, message_id: str):
    """Get a specific message from a task."""
    message = service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.task_id != task_id:
        raise HTTPException(status_code=404, detail="Message not found in this task")
    return message

@router.delete("/{task_id}/messages/{message_id}")
def delete_task_message(task_id: str, message_id: str):
    """Delete a message from a task."""
    message = service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.task_id != task_id:
        raise HTTPException(status_code=404, detail="Message not found in this task")
        
    success = service.delete_message(message_id)
    return {"message": "Message deleted successfully"}

# Chat endpoint
@router.post("/{task_id}/chat", response_model=ChatResponse)
def chat(task_id: str, request: ChatRequest):
    """Process a chat request for a task."""
    # Check if task exists
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create user message
    user_message = service.create_message(
        task_id=task_id,
        message_data=MessageCreate(
            content=request.query,
            role="user",
            type="text"
        )
    )
    
    # In a real implementation, this would call an AI service
    # For now, just echo back the query
    reply = f"I received: {request.query}"
    
    # Create assistant message
    assistant_message = service.create_message(
        task_id=task_id,
        message_data=MessageCreate(
            content=reply,
            role="assistant",
            type="text"
        )
    )
    
    return ChatResponse(reply=reply, message_id=assistant_message.id) 