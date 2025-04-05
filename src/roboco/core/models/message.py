"""
Message Model

This module defines the Message model which serves both as a domain model and database model.
SQLModel is used to combine Pydantic validation with SQLAlchemy persistence.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, DateTime, Relationship
from pydantic import BaseModel

from roboco.utils.id_generator import generate_short_id

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
    
    # Core fields
    id: str = Field(default_factory=generate_short_id, primary_key=True)
    content: str = Field(..., description="Content of the message")
    role: MessageRole = Field(default=MessageRole.USER, description="Role of the message sender")
    
    # Foreign keys (for database relationships only)
    task_id: str = Field(..., foreign_key="tasks.id", index=True, description="Task this message belongs to")
    
    # Agent identification (essential for multi-agent scenarios)
    agent_id: Optional[str] = Field(default=None, description="ID of the agent that sent this message")
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    
    # Message type (important for rendering and processing)
    type: MessageType = Field(default=MessageType.TEXT, description="Type of message content")
    
    # Metadata for extensibility (allows storing arbitrary data without schema changes)
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="Additional metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "id": self.id,
            "content": self.content,
            "role": self.role,
            "task_id": self.task_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "type": self.type
        }
        
        # Include optional fields only if they have values
        if self.agent_id:
            result["agent_id"] = self.agent_id
            
        if self.meta and len(self.meta) > 0:
            result["meta"] = self.meta
            
        return result

# Note: API models have been moved to roboco.api.models.message 