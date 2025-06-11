"""
Configuration Models

Data models for Roboco configuration files, focusing on team collaboration
rather than rigid workflows.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TeamConfig(BaseModel):
    """Configuration for a collaborative team of agents."""
    name: str
    description: Optional[str] = None
    agents: List[str]  # Agent names/IDs in the team
    collaboration_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Configuration for a collaborative agent."""
    name: str
    role: str
    model: str = "gpt-4"
    
    # Collaboration-specific settings
    collaboration_style: str = "cooperative"  # e.g., "cooperative", "competitive", "supportive"
    
    # Agent-specific details for collaboration
    collaboration_details: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ToolParameterConfig(BaseModel):
    """Configuration for a tool parameter."""
    name: str
    type: str  # JSON Schema type
    description: str
    required: bool = True
    default: Optional[Any] = None

class ToolConfig(BaseModel):
    """Configuration for a single tool."""
    name: str
    description: Optional[str] = None
    # How the tool is invoked, e.g., 'python_class', 'api_endpoint', 'shell_command'
    invocation_type: str
    # Details for invocation, e.g., class_name, module_path, url, command_template
    invocation_details: Dict[str, Any]
    parameters_schema: Optional[List[ToolParameterConfig]] = Field(default_factory=list)
    # Other tool-specific settings like authentication, rate limits, etc.

class RobocoConfig(BaseModel):
    """Root configuration for a Roboco application."""
    version: str = "0.1.0"
    teams: Optional[List[TeamConfig]] = Field(default_factory=list)
    tools: Optional[List[ToolConfig]] = Field(default_factory=list)
    # Global settings like logging, event bus config, context store config
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
