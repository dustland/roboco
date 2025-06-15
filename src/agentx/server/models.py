"""
Server Models

Data models for the AgentX REST API.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Get current UTC datetime - replaces deprecated datetime.now()"""
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRequest(BaseModel):
    """Request to create and run a task"""
    config_path: str = Field(description="Path to the task configuration file")
    task_description: str = Field(description="Description of the task to execute")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for the task")


class TaskResponse(BaseModel):
    """Response from task operations"""
    task_id: str
    status: TaskStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: Optional[datetime] = None


class TaskInfo(BaseModel):
    """Information about a task"""
    task_id: str
    status: TaskStatus
    config_path: str
    task_description: str
    context: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class MemoryRequest(BaseModel):
    """Request for memory operations"""
    task_id: str
    agent_id: Optional[str] = Field(default=None, description="Agent ID for agent-specific memory operations")
    content: Optional[str] = Field(default=None, description="Content to add to memory")
    query: Optional[str] = Field(default=None, description="Query to search memory")


class MemoryResponse(BaseModel):
    """Response from memory operations"""
    task_id: str
    agent_id: Optional[str] = None
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=utc_now)
    version: str = "0.4.0"
    active_tasks: int = 0 