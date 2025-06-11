"""
Server Models

Data models for the RoboCo server including session management.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from uuid import uuid4


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class SessionConfig(BaseModel):
    """Configuration for a session"""
    max_idle_time: timedelta = Field(default=timedelta(hours=1), description="Maximum idle time before session expires")
    max_session_time: timedelta = Field(default=timedelta(hours=8), description="Maximum total session time")
    auto_cleanup: bool = Field(default=True, description="Whether to auto-cleanup expired sessions")
    context_limit: int = Field(default=1000, description="Maximum context entries per session")
    
    class Config:
        json_encoders = {
            timedelta: lambda td: td.total_seconds()
        }


class SessionInfo(BaseModel):
    """Information about a session"""
    session_id: str = Field(default_factory=lambda: str(uuid4()))
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Statistics
    total_requests: int = 0
    total_collaborations: int = 0
    context_entries: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class CollaborationRequest(BaseModel):
    """Request to start a collaboration"""
    session_id: str
    team_config_path: str
    task: str
    context: Optional[Dict[str, Any]] = None
    stream: bool = False


class CollaborationResponse(BaseModel):
    """Response from a collaboration"""
    collaboration_id: str
    session_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ContextRequest(BaseModel):
    """Request for context operations"""
    session_id: str
    operation: str  # save, load, list, delete
    key: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ContextResponse(BaseModel):
    """Response from context operations"""
    session_id: str
    operation: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    
    
class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "0.4.0"
    active_sessions: int = 0
    total_sessions: int = 0
    uptime: timedelta = Field(default_factory=lambda: timedelta(0))
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            timedelta: lambda td: td.total_seconds()
        } 