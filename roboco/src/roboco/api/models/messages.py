"""API models for message handling."""

from typing import Optional
from pydantic import BaseModel

from roboco.core.types import AgentRole

class MessageRequest(BaseModel):
    """Request model for sending messages between agents."""
    from_role: AgentRole
    to_role: AgentRole
    message: str

class MessageResponse(BaseModel):
    """Response model for agent messages."""
    response: Optional[str]
    success: bool
    error: Optional[str] = None 