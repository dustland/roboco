"""Core types and enums for RoboCo."""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class AgentRole(str, Enum):
    """Enum for different agent roles in the system."""
    HUMAN = "human"
    EXECUTIVE_BOARD = "executive_board"
    PRODUCT_MANAGER = "product_manager"

class LLMConfig(BaseModel):
    """LLM configuration."""
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 0.95
    timeout: int = 600

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    role: AgentRole
    name: str
    system_message: str
    human_input_mode: str = "NEVER"
    llm_config: Optional[Dict[str, Any]] = None
    is_termination_msg: Optional[str] = None 