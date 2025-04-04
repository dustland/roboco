"""
Chat API Schema

This module defines the Pydantic models for chat-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request to initiate a chat with the project agent."""
    query: str
    task_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response from chat API."""
    conversation_id: str
    message: str
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "completed"


class ConversationItem(BaseModel):
    """Brief information about a conversation for listing."""
    id: str
    title: str
    created_at: str
    updated_at: str
    project_id: Optional[str] = None
    last_message: Optional[str] = None
    status: str = "completed"


class ConversationStatus(BaseModel):
    """Status of a conversation."""
    id: str
    status: str
    message: str
    progress: Optional[float] = None
    created_at: str
    updated_at: str
