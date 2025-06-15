from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

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