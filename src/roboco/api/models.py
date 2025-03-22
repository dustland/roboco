"""
API Data Models

This module defines the data models used by the RoboCo API.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

class JobRequest(BaseModel):
    """Request model for starting a new job."""
    team: str = Field(..., description="Team configuration to use")
    initial_agent: str = Field(..., description="Name of the agent to start the process")
    query: str = Field(..., description="Initial query or instruction to process")
    output_dir: Optional[str] = Field(None, description="Custom output directory name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Additional parameters for the team")

class JobStatus(BaseModel):
    """Status of a running or completed job."""
    job_id: str
    team: str
    status: str = Field(..., description="Current status (running, completed, failed)")
    start_time: datetime
    end_time: Optional[datetime] = None
    last_updated: datetime
    output_dir: str
    initial_agent: str
    query: str
    current_agent: Optional[str] = None
    progress: Optional[float] = Field(None, description="Progress from 0.0 to 1.0")
    error: Optional[str] = None
    result: Optional[Any] = None

class TeamInfo(BaseModel):
    """Information about an available team."""
    key: str
    name: str
    description: str
    roles: List[str]
    tools: List[str]

class ArtifactInfo(BaseModel):
    """Information about a generated artifact."""
    name: str
    path: str
    size: int
    last_modified: datetime
    type: str = Field(..., description="Type of artifact (file or directory)")

class ToolRegistration(BaseModel):
    """Information for registering a tool with an agent."""
    tool_name: str
    agent_name: str
    parameters: Optional[Dict[str, Any]] = None

class AgentStatusUpdate(BaseModel):
    """Update for a job's current agent and progress."""
    job_id: str
    current_agent: str
    progress: Optional[float] = None
    status_message: Optional[str] = None 