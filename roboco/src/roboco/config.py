"""Configuration management for RoboCo."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel

class LLMConfig(BaseModel):
    """LLM configuration."""
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 0.95
    timeout: int = 600

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    llm: LLMConfig = LLMConfig()
    additional_config: Dict[str, Any] = {}

class RoboCoConfig(BaseModel):
    """Main configuration for RoboCo."""
    human: AgentConfig = AgentConfig()
    executive_board: AgentConfig = AgentConfig()
    product_manager: AgentConfig = AgentConfig()

def load_config(config_path: Optional[str] = None) -> RoboCoConfig:
    """Load configuration from file or use defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        return RoboCoConfig(**config_dict)
    return RoboCoConfig() 