from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class Event(BaseModel):
    """
    Base model for all events within the Roboco system.
    Events are immutable once created.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str # Dotted notation, e.g., "task.started", "task.completed"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None # e.g., "Agent/Planner", "Tool/WebSearch", "System"
    data: Dict[str, Any] = Field(default_factory=dict) # Arbitrary data payload

    class Config:
        frozen = True # Enforce immutability
