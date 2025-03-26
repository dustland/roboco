"""
Chat API Schema

This module defines the Pydantic models for chat-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request to initiate a chat with the project agent for project creation."""
    query: str = Field(..., description="The query to process")
    teams: Optional[List[str]] = Field(None, description="Optional specific teams to assign")
    conversation_id: Optional[str] = Field(None, description="Optional ID to continue existing conversation")


class ChatResponse(BaseModel):
    """Response from project chat API."""
    conversation_id: str = Field(..., description="Unique identifier for the conversation")
    project_id: Optional[str] = Field(None, description="Project ID if a project was created")
    message: str = Field(..., description="Response message")
    project_details: Optional[Dict[str, Any]] = Field(None, description="Details about the created project")
    status: str = Field(..., description="Status of the conversation")
    
    @classmethod
    def from_chat_result(cls, result: Dict[str, Any], conversation_id: str):
        """Convert chat result dictionary to API response model."""
        return cls(
            conversation_id=conversation_id,
            project_id=result.get("project_id"),
            message=result.get("message", ""),
            project_details=result.get("project_details"),
            status=result.get("status", "completed")
        )
