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


def get_llm_config(config: RobocoConfig) -> Dict[str, Any]:
    """
    Create an autogen-compatible LLM configuration from a RobocoConfig instance.
    
    Args:
        config: RobocoConfig instance
        
    Returns:
        Dictionary containing the LLM configuration for autogen
    """
    # Extract LLM configuration
    llm_config = config.llm
    
    # Create an autogen-compatible configuration
    autogen_config = {
        "config_list": [
            {
                "model": llm_config.model,
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
            }
        ],
        "temperature": llm_config.temperature,
        "max_tokens": llm_config.max_tokens,
    }
    
    return autogen_config


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
