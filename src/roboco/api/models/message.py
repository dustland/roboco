"""
Message API Models

This module defines the Pydantic models for message-related API requests and responses.
These models are used for validation and serialization at the API boundary.
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel

from roboco.core.models.message import MessageRole, MessageType, Message


class MessageCreate(BaseModel):
    """API model for creating a message."""
    content: str
    task_id: str
    role: MessageRole = MessageRole.USER
    type: MessageType = MessageType.TEXT
    parent_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_responses: Optional[List[Dict[str, Any]]] = None
    agent_id: Optional[str] = None
    
    def to_db_model(self) -> Message:
        """Convert API model to database model."""
        data = self.model_dump(exclude_unset=True)
        return Message(**data)


class MessageResponse(BaseModel):
    """API model for message responses."""
    id: str
    content: str
    role: str
    task_id: str
    timestamp: str
    parent_id: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    type: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_responses: Optional[List[Dict[str, Any]]] = None
    agent_id: Optional[str] = None
    
    @classmethod
    def from_db_model(cls, message: Message) -> "MessageResponse":
        """Convert database model to API response model."""
        return cls(
            id=message.id,
            content=message.content,
            role=message.role,
            task_id=message.task_id,
            timestamp=message.timestamp.isoformat() if message.timestamp else None,
            parent_id=message.parent_id,
            meta=message.meta,
            type=message.type,
            tool_calls=message.tool_calls,
            tool_responses=message.tool_responses,
            agent_id=message.agent_id
        )
    
    class Config:
        """Pydantic config for the model."""
        from_attributes = True 