"""
Configuration management for Roboco.

This module handles loading and managing configuration from various sources:
- Environment variables
- .env files
- YAML configuration files
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import yaml
from .models import RobocoConfig


def load_env_vars() -> None:
    """Load environment variables from .env file if it exists."""
    load_dotenv()  # Loads .env from current directory


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    config_paths = [
        Path.cwd() / 'config.yaml',
        Path.cwd() / 'config' / 'config.yaml',
        Path.home() / '.config' / 'roboco' / 'config.yaml',
        Path('/etc/roboco/config.yaml')
    ]
    
    for path in config_paths:
        if path.exists():
            return path
            
    # If no config file exists, return the default location
    return Path.cwd() / 'config.yaml'


def process_env_vars(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process environment variable placeholders in configuration.
    Replaces ${VAR} with the value of the environment variable VAR.
    
    Args:
        config_data: Dictionary containing configuration data
        
    Returns:
        Dictionary with environment variables processed
    """
    if not config_data:
        return config_data
        
    result = {}
    for key, value in config_data.items():
        if isinstance(value, dict):
            result[key] = process_env_vars(value)
        elif isinstance(value, str) and "${" in value and "}" in value:
            # Process environment variable
            env_var = value.split("${")[1].split("}")[0]
            env_value = os.environ.get(env_var)
            if env_value:
                result[key] = env_value
            else:
                result[key] = value  # Keep original if not found
        else:
            result[key] = value
    return result


def load_config(config_path: Optional[Path] = None) -> RobocoConfig:
    """
    Load configuration from YAML file and environment variables.
    
    Args:
        config_path: Optional path to config file. If not provided,
                    will search in standard locations.
                    
    Returns:
        RobocoConfig: Loaded configuration object
    """
    # Load environment variables first
    load_env_vars()
    
    # Get config file path
    if config_path is None:
        config_path = get_config_path()
    
    # Load YAML config if it exists
    config_data: Dict[str, Any] = {}
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            
    # Process environment variables in config
    config_data = process_env_vars(config_data)
    
    # Create config object
    config = RobocoConfig(**config_data)
    
    return config


def save_config(config: RobocoConfig, config_path: Optional[Path] = None) -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration object to save
        config_path: Optional path to save config to. If not provided,
                    will use the default location.
    """
    if config_path is None:
        config_path = get_config_path()
    
    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert config to dict and save as YAML
    config_dict = config.model_dump(exclude_none=True)
    with open(config_path, 'w') as f:
        yaml.dump(config_dict, f, default_flow_style=False)


def create_default_config() -> RobocoConfig:
    """Create and save a default configuration."""
    config = RobocoConfig()
    save_config(config)
    return config


def get_llm_config(config: Optional[RobocoConfig] = None) -> Dict[str, Any]:
    """
    Create an LLM configuration dictionary suitable for agent use.
    
    Args:
        config: RobocoConfig instance (if None, will call load_config)
        
    Returns:
        Dictionary containing the LLM configuration for agents
    """
    if config is None:
        config = load_config()
    
    # Extract base LLM configuration
    llm_section = config.llm
    
    # Create the config dictionary with just the essential parameters
    agent_llm_config = {
        "model": llm_section.model,
        "api_key": llm_section.api_key,
        "temperature": llm_section.temperature,
        "max_tokens": llm_section.max_tokens,
    }
    
    # Add base_url if provided
    if llm_section.base_url:
        agent_llm_config["base_url"] = llm_section.base_url
    
    return agent_llm_config


def get_workspace(config: Optional[RobocoConfig] = None) -> Path:
    """
    Get the path to the workspace root directory.
    
    Args:
        config: RobocoConfig instance (if None, will call load_config)
        
    Returns:
        Path to the workspace root directory
    """
    if config is None:
        config = load_config()
    
    workspace_path = Path(config.workspace_root)
    
    # If it's a relative path, make it relative to the current directory
    if not workspace_path.is_absolute():
        workspace_path = Path.cwd() / workspace_path
    else:
        # If it's an absolute path with ~ for home dir, expand it
        workspace_path = workspace_path.expanduser()
    
    # Resolve to absolute path
    workspace_path = workspace_path.resolve()
    
    # Ensure workspace exists
    if not workspace_path.exists():
        workspace_path.mkdir(parents=True, exist_ok=True)
    
    return workspace_path
