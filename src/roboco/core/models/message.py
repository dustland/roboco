"""
Message Model

This module defines the Message model which serves both as a domain model and database model.
SQLModel is used to combine Pydantic validation with SQLAlchemy persistence.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4
from sqlmodel import SQLModel, Field, Column, JSON, DateTime, Relationship
from pydantic import BaseModel

if TYPE_CHECKING:
    from roboco.core.models.task import Task

class MessageRole(str, Enum):
    """Role of a message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class MessageType(str, Enum):
    """Type of message content."""
    TEXT = "text"
    CODE = "code"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"

class ToolCall(BaseModel):
    """Tool call definition based on AutoGen's approach."""
    id: str
    name: str
    function: Dict[str, Any]
    type: str = "function"

class Message(SQLModel, table=True):
    """
    Unified Message model for both domain logic and database persistence.
    
    This model serves as a single source of truth for message data.
    """
    # Database table name
    __tablename__ = "messages"
    
    # Common fields
    id: str = Field(default_factory=lambda: str(uuid4())[:8], primary_key=True)
    content: str = Field(..., description="Content of the message")
    role: MessageRole = Field(default=MessageRole.USER, description="Role of the message sender")
    task_id: str = Field(..., foreign_key="tasks.id", description="Task this message belongs to")
    
    # Fields for threading and tool use (based on autogen approach)
    parent_id: Optional[str] = Field(default=None, description="Parent message ID for threading")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON), 
                                                      description="Tool calls in this message")
    tool_responses: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON),
                                                         description="Tool responses for this message")
    
    # Agent identification
    agent_id: Optional[str] = Field(default=None, description="ID of the agent that sent this message")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    
    # Message type
    type: MessageType = Field(default=MessageType.TEXT, description="Type of message content")
    
    # Metadata for extensibility
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="Additional metadata")
    
    # File related fields (if this message references a file)
    file_path: Optional[str] = Field(default=None, description="Path to a file if this message is about a file")
    
    # Relationships
    task: Optional["Task"] = Relationship(back_populates="messages")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "type": self.type,
            "meta": self.meta
        }
        
        # Include optional fields only if they have values
        if self.agent_id:
            result["agent_id"] = self.agent_id
            
        if self.parent_id:
            result["parent_id"] = self.parent_id
            
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
            
        if self.tool_responses:
            result["tool_responses"] = self.tool_responses
            
        if self.file_path:
            result["file_path"] = self.file_path
            
        return result

# Note: API models have been moved to roboco.api.models.message 