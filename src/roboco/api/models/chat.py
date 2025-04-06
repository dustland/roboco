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
    message: str
    project_id: str
    task_id: Optional[str] = None
    status: str = "completed"

