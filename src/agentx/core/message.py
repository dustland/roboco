from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal, TYPE_CHECKING
from ..utils.id import generate_short_id

if TYPE_CHECKING:
    from .tool import ToolCall

# This file defines the core data structures for the AgentX framework,
# as specified in design document 03-data-and-events.md.

# --- Core Data Structures ---

# Note: ToolCall and ToolResult are defined in core.tool, not here. This separation is intentional:
# - ToolCall/ToolResult = tool execution models (core.tool)
# - ToolCallPart/ToolResultPart = conversation representations (here in message.py)
# The conversation parts are self-contained and don't depend on tool execution models

class Artifact(BaseModel):
    """Artifact reference with versioning and metadata."""
    uri: str  # e.g., "file://artifacts/main.py"
    mime_type: str
    size_bytes: Optional[int] = None
    description: Optional[str] = None
    version: Optional[str] = None  # For artifact versioning
    checksum: Optional[str] = None  # For integrity verification
    metadata: Dict[str, Any] = Field(default_factory=dict)  # Extensible metadata
    created_by: Optional[str] = None  # Agent or tool that created it
    tags: List[str] = Field(default_factory=list)  # For categorization and search

# --- TaskStep and its Parts ---

class TextPart(BaseModel):
    """Text content part with language and confidence support."""
    type: Literal["text"] = "text"
    text: str
    language: Optional[str] = None  # For multilingual support
    confidence: Optional[float] = None  # LLM confidence score

class ToolCallPart(BaseModel):
    """Tool call request part - conversation representation."""
    type: Literal["tool_call"] = "tool_call"
    tool_call_id: str
    tool_name: str
    args: Dict[str, Any]
    expected_output_type: Optional[str] = None

class ToolResultPart(BaseModel):
    """Tool execution result part."""
    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    tool_name: str
    result: Any
    is_error: bool = False

class ArtifactPart(BaseModel):
    """Artifact reference part."""
    type: Literal["artifact"] = "artifact"
    artifact: Artifact

class ImagePart(BaseModel):
    """Image content part with metadata."""
    type: Literal["image"] = "image"
    image_url: str  # Can be data URL or artifact reference
    alt_text: Optional[str] = None
    dimensions: Optional[Dict[str, int]] = None  # width, height
    format: Optional[str] = None  # png, jpg, etc.

class AudioPart(BaseModel):
    """Audio content part with metadata."""
    type: Literal["audio"] = "audio"
    audio_url: str  # Can be data URL or artifact reference
    transcript: Optional[str] = None
    duration_seconds: Optional[float] = None
    format: Optional[str] = None  # mp3, wav, etc.
    sample_rate: Optional[int] = None

class MemoryReference(BaseModel):
    """Memory reference with relevance scoring."""
    memory_id: str
    memory_type: str  # "short_term", "long_term", "semantic", "episodic"
    relevance_score: Optional[float] = None
    retrieval_query: Optional[str] = None

class MemoryPart(BaseModel):
    """Memory operation part."""
    type: Literal["memory"] = "memory"
    operation: str  # "store", "retrieve", "search", "consolidate"
    references: List[MemoryReference]
    content: Optional[Dict[str, Any]] = None

class GuardrailCheck(BaseModel):
    """Individual guardrail check result."""
    check_id: str
    check_type: str  # "input_validation", "content_filter", "rate_limit", "policy"
    status: str  # "passed", "failed", "warning"
    message: Optional[str] = None
    policy_violated: Optional[str] = None
    severity: Optional[str] = None  # "low", "medium", "high", "critical"

class GuardrailPart(BaseModel):
    """Guardrail check results part."""
    type: Literal["guardrail"] = "guardrail"
    checks: List[GuardrailCheck]
    overall_status: str  # "passed", "failed", "warning"

ConversationPart = Union[TextPart, ToolCallPart, ToolResultPart]

class TaskStep(BaseModel):
    """A single step in a task's conversation history."""
    step_id: str = Field(default_factory=lambda: f"step_{datetime.now().timestamp()}")
    agent_name: str
    parts: List[ConversationPart]
    timestamp: datetime = Field(default_factory=datetime.now)

# --- Streaming Models ---

class StreamChunk(BaseModel):
    """
    Token-by-token message streaming from LLM.
    
    This is Channel 1 of the dual-channel system - provides low-latency
    UI updates for "typing" effect. This is message streaming, not events.
    """
    type: Literal["content_chunk"] = "content_chunk"
    step_id: str  # Links to the TaskStep being generated
    agent_name: str
    text: str
    is_final: bool = False  # True for the last chunk of a response
    token_count: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StreamError(BaseModel):
    """
    Error in message streaming.
    """
    type: Literal["stream_error"] = "stream_error"
    step_id: str
    agent_name: str
    error_message: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StreamComplete(BaseModel):
    """
    Message streaming completion marker.
    """
    type: Literal["stream_complete"] = "stream_complete"
    step_id: str
    agent_name: str
    total_tokens: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 