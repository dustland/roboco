from typing import Optional, Dict, Any, Union
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class Message(BaseModel):
    """
    Represents a message exchanged within the Roboco system.
    Messages are immutable once created.
    """
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str  # e.g., "user", "assistant", "system", "tool", "planner", "writer"
    content: Union[str, Dict[str, Any], BaseModel] # Flexible content: text, structured data, or Pydantic model
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Example metadata keys: "tool_id", "tool_call_id", "source_agent_id", "target_agent_id"

    class Config:
        frozen = True # Enforce immutability
        arbitrary_types_allowed = True # To allow BaseModel in content
