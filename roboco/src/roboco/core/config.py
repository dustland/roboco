"""Configuration management for RoboCo."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from pydantic import BaseModel

from .types import LLMConfig, AgentConfig

class RoboCoConfig(BaseModel):
    """Main configuration for RoboCo."""
    human: AgentConfig = AgentConfig()
    executive_board: AgentConfig = AgentConfig()
    product_manager: AgentConfig = AgentConfig()

def load_config(config_path: Optional[str] = None) -> RoboCoConfig:
    """Load configuration from file or use defaults.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        RoboCoConfig object with loaded configuration
        
    Raises:
        FileNotFoundError: If config_path is provided but file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if config_path:
        config_path = os.path.expanduser(config_path)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            try:
                config_dict = yaml.safe_load(f)
                return RoboCoConfig(**config_dict)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing configuration file: {str(e)}")
            
    # Use default configuration
    return RoboCoConfig() 