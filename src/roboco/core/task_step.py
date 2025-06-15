from typing import Literal, Any, List, Optional, Union
from pydantic import BaseModel, Field
import uuid
import time

# --- Tool-related parts ---

class ToolCall(BaseModel):
    """Represents a request to call a tool."""
    id: str = Field(default_factory=lambda: f"tool_{uuid.uuid4().hex}")
    tool_name: str
    args: dict[str, Any]

class ToolResult(BaseModel):
    """Represents the result of a tool call."""
    tool_call_id: str
    result: Any
    is_error: bool = False

# --- Content parts that make up a TaskStep ---

class TextPart(BaseModel):
    """A part of a task step containing plain text."""
    type: Literal["text"] = "text"
    text: str

class ToolCallPart(BaseModel):
    """A part of a task step representing a tool call."""
    type: Literal["tool_call"] = "tool_call"
    tool_call: ToolCall

class ToolResultPart(BaseModel):
    """A part of a task step representing a tool result."""
    type: Literal["tool_result"] = "tool_result"
    tool_result: ToolResult

StepPart = Union[TextPart, ToolCallPart, ToolResultPart]

# --- The main TaskStep model ---

class TaskStep(BaseModel):
    """
    The fundamental unit of the execution history. A TaskStep represents a
    single, discrete event or state change in the execution of a task.
    """
    id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex}")
    parent_id: Optional[str] = None
    agent_name: str
    created_at: float = Field(default_factory=time.time)
    parts: List[StepPart]
    metadata: dict[str, Any] = Field(default_factory=dict) 