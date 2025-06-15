from pydantic import BaseModel, Field
from typing import List, Dict

class AgentConfig(BaseModel):
    name: str
    system_message_prompt: str
    model: str
    tools: List[str] = []

class ToolDefinition(BaseModel):
    source: str

class TeamConfig(BaseModel):
    version: str
    name: str
    max_rounds: int = 10
    agents: List[AgentConfig]
    tool_definitions: Dict[str, ToolDefinition] = Field(default_factory=dict) 