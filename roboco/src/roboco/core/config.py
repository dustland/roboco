"""
Configuration Management Module

This module provides utilities for loading and managing configuration for roboco agents.
"""

import os
import tomli
from pathlib import Path
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    # Try importing from ag2 first (preferred package name)
    from ag2 import config_list_from_json, config_list_from_dotenv
except ImportError:
    # Fall back to autogen if ag2 is not available
    from autogen import config_list_from_json, config_list_from_dotenv


def load_config_from_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a TOML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration
    """
    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return {}


def get_llm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an autogen-compatible LLM configuration from a configuration dictionary.
    
    Args:
        config: Configuration dictionary (usually loaded from a TOML file)
        
    Returns:
        Dictionary containing the LLM configuration for autogen
    """
    # Extract LLM configuration
    llm_section = config.get("llm", {})
    
    # Create an autogen-compatible configuration
    llm_config = {
        "config_list": [
            {
                "model": llm_section.get("model", "gpt-4"),
                "api_key": os.environ.get("OPENAI_API_KEY", ""),
            }
        ],
        "temperature": llm_section.get("temperature", 0.7),
        "max_tokens": llm_section.get("max_tokens", 4000),
    }
    
    return llm_config


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
