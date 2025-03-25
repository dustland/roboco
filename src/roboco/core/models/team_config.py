"""
Team Configuration Schema

This module defines the schema and validation for team configurations.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TeamConfig(BaseModel):
    """Configuration for a team of agents.
    
    This standardizes team configuration across different team types.
    Tasks are implemented directly within each team class rather than
    being configured here, to simplify the configuration structure.
    """
    name: str = Field(
        default="",
        description="Name of the team"
    )
    description: str = Field(
        default="",
        description="Description of the team's purpose"
    )
    roles: List[str] = Field(
        default_factory=list,
        description="List of roles in this team"
    )
    orchestrator_name: Optional[str] = Field(
        default=None,
        description="Name of the agent to use as orchestrator (if any)"
    )
    tool_executor: Optional[str] = Field(
        default=None,
        description="Name of the agent to use as tool executor"
    )
    workflow: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Definition of the agent workflow/handoffs"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tools available to the team"
    )
    agent_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configurations for specific agents in the team"
    )
    output_dir: str = Field(
        default="workspace/team_output",
        description="Directory for team outputs"
    )
    
    class Config:
        extra = 'allow'  # Allow extra fields for team-specific configs 