"""
Configuration Management Module

This module provides utilities for loading and managing configuration for roboco agents.
"""

import os
import tomli
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger
from dotenv import load_dotenv

# ag2 and autogen are identical packages
from autogen import config_list_from_json, config_list_from_dotenv

from roboco.core.models import RobocoConfig, LLMConfig


def load_config(config_path: Optional[str] = None) -> RobocoConfig:
    """
    Load configuration from environment variables and TOML file.
    
    Args:
        config_path: Optional path to the configuration file
        
    Returns:
        Validated RobocoConfig instance
    """
    # Load environment variables first
    load_dotenv()
    
    if config_path is None:
        # Try to find a config file in standard locations
        search_paths = [
            Path("./config.toml"),         # Current directory
            Path("config/config.toml"),    # Project config directory
            Path(os.path.expanduser("~/.config/roboco/config.toml")),  # User config
            Path("/etc/roboco/config.toml"),  # System config
        ]
        
        for path in search_paths:
            if path.exists():
                config_path = str(path)
                break
    
    if config_path and Path(config_path).exists():
        try:
            with open(config_path, "rb") as f:
                config_dict = tomli.load(f)
            
            # Validate configuration using Pydantic model
            config = RobocoConfig(**config_dict)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
    else:
        logger.warning("No configuration file found, using default configuration")
    
    # Return default configuration
    return RobocoConfig()


def get_llm_config(config: Optional[RobocoConfig] = None) -> Dict[str, Any]:
    """
    Create an LLM configuration dictionary suitable for autogen/AG2 agents.
    
    This function extracts LLM configuration from the config.toml file and 
    formats it for use with autogen agents.
    
    Args:
        config: RobocoConfig instance (if None, will call load_config)
        
    Returns:
        Dictionary containing the LLM configuration for agents
    """
    if config is None:
        config = load_config()
    
    # Extract LLM configuration from the toml config
    llm_section = config.llm
    
    # Create a direct config dictionary for agents
    agent_llm_config = {
        "model": llm_section.model,
        "api_key": llm_section.api_key,  # Use API key directly from config
        "temperature": llm_section.temperature,
    }
    
    # Add base_url if provided in config
    if hasattr(llm_section, 'base_url') and llm_section.base_url:
        agent_llm_config["base_url"] = llm_section.base_url
    
    # Add max_tokens if provided in config
    if hasattr(llm_section, 'max_tokens') and llm_section.max_tokens:
        agent_llm_config["max_tokens"] = llm_section.max_tokens
    
    return agent_llm_config


def load_env_variables(project_root: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file.
    
    Args:
        project_root: Root directory of the project (optional)
    """
    try:
        from dotenv import load_dotenv
        
        if project_root is None:
            # Try to determine project root
            current_dir = Path.cwd()
            while current_dir.name != "roboco" and current_dir.parent != current_dir:
                current_dir = current_dir.parent
            project_root = current_dir
            
        env_path = project_root / ".env"
        
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning("No .env file found, using existing environment variables")
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env loading")
