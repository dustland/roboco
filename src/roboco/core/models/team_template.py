"""
Team template model definitions.
"""
from typing import List, Set

from pydantic import BaseModel, Field


class TeamCapabilities(BaseModel):
    """Represents the capabilities required for a team."""
    required_tools: Set[str] = Field(default_factory=set)
    complexity: str = "medium"
    domain_knowledge: List[str] = Field(default_factory=list)
    specialized_skills: List[str] = Field(default_factory=list)


class TeamTemplate(BaseModel):
    """Template for creating a team."""
    agents: List[str]
    tools: List[str]
    workflow: str
    description: str
    capabilities: TeamCapabilities = Field(default_factory=TeamCapabilities)
