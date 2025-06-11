from typing import Dict, Any, Optional, Literal
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

class Event(BaseModel):
    """
    Base model for all events within the Roboco system.
    Events are immutable once created.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str # Dotted notation, e.g., "system.startup", "agent.message.received"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: Optional[str] = None # e.g., "Agent/Planner", "Tool/WebSearch", "System"
    data: Dict[str, Any] = Field(default_factory=dict) # Arbitrary data payload

    class Config:
        frozen = True # Enforce immutability

# --- Generic Event Categories (Examples) ---
# Specific events can inherit from these or directly from Event.

class SystemEvent(Event):
    """Base for system-level events (e.g., startup, shutdown, error)."""
    # Subclasses should override event_type, e.g., event_type: Literal["system.started"] = "system.started"
    pass

class AgentEvent(Event):
    """Base for events originating from or related to agents."""
    agent_id: Optional[str] = None
    team_id: Optional[str] = None
    pass

class ToolEvent(Event):
    """Base for events originating from or related to tools."""
    tool_name: Optional[str] = None
    tool_id: Optional[str] = None # If tools have unique IDs
    tool_call_id: Optional[str] = None # Correlate with a specific tool invocation
    pass

# --- Example Specific Events (can be expanded significantly) ---

class MessageSentEvent(AgentEvent):
    event_type: Literal["agent.message.sent"] = "agent.message.sent"
    message_id: str
    sender_agent_id: str
    recipient_agent_id: Optional[str] = None # For direct messages

class MessageReceivedEvent(AgentEvent):
    event_type: Literal["agent.message.received"] = "agent.message.received"
    message_id: str
    sender_agent_id: Optional[str] = None # If message is from system or external
    recipient_agent_id: str

class ToolCallInitiatedEvent(ToolEvent):
    event_type: Literal["tool.call.initiated"] = "tool.call.initiated"
    agent_id: str # The agent calling the tool
    input_args: Dict[str, Any]

class ToolCallCompletedEvent(ToolEvent):
    event_type: Literal["tool.call.completed"] = "tool.call.completed"
    agent_id: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

class SystemStartedEvent(SystemEvent):
    event_type: Literal["system.started"] = "system.started"

class SystemShutdownEvent(SystemEvent):
    event_type: Literal["system.shutdown"] = "system.shutdown"
    exit_code: Optional[int] = None

class ErrorOccurredEvent(SystemEvent): # Could also be AgentErrorEvent or ToolErrorEvent
    event_type: Literal["system.error.occurred"] = "system.error.occurred"
    error_message: str
    error_type: Optional[str] = None # e.g., "ConfigurationError", "ToolExecutionError"
    details: Optional[Dict[str, Any]] = None
