"""
AG2 Core Integration Module

This module provides direct integration with the AG2 framework (autogen),
making AG2's components available as the foundation for roboco's agents and tools.
"""

import os
import tomli
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
from loguru import logger

# Directly import AG2 framework components as roboco's foundation
try:
    from autogen import (
        AssistantAgent,
        UserProxyAgent,
        ConversableAgent,
        GroupChat,
        GroupChatManager,
        initiate_chats,
        config_list_from_json,
        config_list_from_dotenv
    )
except ImportError:
    logger.error("AG2 framework (autogen) is not installed. Please install it with: pip install pyautogen")
    raise

# Export AG2 components directly to make them available through roboco
__all__ = [
    "AssistantAgent",
    "UserProxyAgent",
    "ConversableAgent",
    "GroupChat",
    "GroupChatManager",
    "initiate_chats",
    "config_list_from_json",
    "config_list_from_dotenv",
    "load_config_from_toml",
]

def load_config_from_toml(config_path: str) -> Dict[str, Any]:
    """
    Load AG2 configuration from a TOML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary compatible with AG2
    """
    try:
        with open(config_path, "rb") as f:
            config_data = tomli.load(f)
        
        # Extract LLM configuration
        llm_config = config_data.get("llm", {})
        
        # Check for API keys referenced as environment variables
        for key, value in llm_config.items():
            if isinstance(value, str) and value.startswith("$"):
                env_var = value[1:]
                llm_config[key] = os.environ.get(env_var, "")
        
        # Create AG2-compatible configuration
        api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Format as expected by autogen
        config_dict = {
            "model": llm_config.get("model", "gpt-4o"),
            "temperature": llm_config.get("temperature", 0.7),
            "max_tokens": llm_config.get("max_tokens", 4000),
            "api_key": api_key,
        }
        
        return {"config_list": [config_dict]}
    
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        raise
