from pydantic import BaseModel, Field
from typing import List, Dict, Any

class Agent(BaseModel):
    """
    Represents a configurable agent within a team.
    
    This is a data-only class that holds the configuration for an agent.
    The Orchestrator uses this configuration to execute the agent's logic.
    """
    name: str
    system_message: str = "You are a helpful assistant."
    model: str = "claude-3-haiku-20240307"
    # In the future, we can add agent-specific tools, memory configs, etc.
    tools: List[Dict[str, Any]] = Field(default_factory=list)

def create_assistant_agent(name: str, system_message: str = "") -> Agent:
    """
    Backwards compatibility function to create a basic assistant agent.
    """
    return Agent(
        name=name,
        system_message=system_message or "You are a helpful assistant."
    ) 