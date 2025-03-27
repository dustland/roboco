"""
Configuration management for Roboco.

This module handles loading and managing configuration from various sources:
- Environment variables
- .env files
- YAML configuration files
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Union, List, TypeVar, Generic, cast
from dotenv import load_dotenv
import yaml
from loguru import logger
from roboco.core.models import RobocoConfig, RoleConfig, AgentConfig

# Type variables for generic functions
T = TypeVar('T')


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


def load_config(config_path: Optional[Union[str, Path]] = None) -> RobocoConfig:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Optional path to config file. If not provided, will search for config.
        
    Returns:
        A RobocoConfig object that provides direct access to nested config properties
    """
    # Load environment variables first
    load_env_vars()
    
    # Determine config path
    if config_path is None:
        path = get_config_path()
    elif isinstance(config_path, str):
        path = Path(config_path)
    else:
        path = config_path
    
    # If config file does not exist, create default
    if not path.exists():
        return create_default_config()
    
    # Load and parse the config file
    with open(path, 'r') as f:
        raw_config = yaml.safe_load(f)
    
    if not raw_config:
        raw_config = {}
    
    # Replace environment variables
    raw_config = process_env_vars(raw_config)
    
    # Create a validated configuration object for standard fields
    # using RobocoConfig, which validates the schema
    validated_fields = {}
    extra_fields = {}
    
    # Separate standard fields from extra fields
    for key, value in raw_config.items():
        if key in RobocoConfig.model_fields:
            validated_fields[key] = value
        else:
            extra_fields[key] = value
    
    # Create the standard config
    standard_config = RobocoConfig(**validated_fields)
    
    return standard_config


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
    
    # Save as YAML
    with open(config_path, 'w') as f:
        yaml.dump(config.model_dump(exclude_none=True), f, default_flow_style=False)


def create_default_config() -> RobocoConfig:
    """Create and save a default configuration."""
    config = RobocoConfig()
    save_config(config)
    return config


def get_llm_config(config: Optional[RobocoConfig] = None, provider: str = "llm") -> Dict[str, Any]:
    """
    Create an LLM configuration dictionary suitable for agent use.
    
    Args:
        config: RobocoConfig instance (if None, will call load_config)
        provider: The LLM provider to use (e.g., "llm", "openai", "deepseek", "ollama")
                 This allows different agents to use different LLM providers.
        
    Returns:
        Dictionary containing the LLM configuration for agents
    """
    if config is None:
        config = load_config()
    
    # Extract base LLM configuration
    llm_section = config.llm
    
    # If provider is the default "llm", use the base configuration
    if provider == "llm":
        # Create the config dictionary with just the essential parameters
        agent_llm_config = {
            "model": llm_section.model,
            "api_key": llm_section.api_key,
            "temperature": llm_section.temperature,
            "max_tokens": llm_section.max_tokens,
        }
        
        # Add base_url if provided
        if hasattr(llm_section, 'base_url') and llm_section.base_url:
            agent_llm_config["base_url"] = llm_section.base_url
    
    # Otherwise, use a specific provider's configuration
    else:
        # Check if the provider configuration exists
        if not hasattr(llm_section, provider) or getattr(llm_section, provider) is None:
            raise ValueError(f"LLM provider '{provider}' not found in configuration")
        
        provider_config = getattr(llm_section, provider)
        
        # Create the config dictionary with provider-specific parameters
        agent_llm_config = {
            "model": provider_config.get("model", llm_section.model),
            "api_key": provider_config.get("api_key", llm_section.api_key),
            "temperature": provider_config.get("temperature", llm_section.temperature),
            "max_tokens": provider_config.get("max_tokens", llm_section.max_tokens),
        }
        
        # Add base_url if provided in the provider config
        if "base_url" in provider_config:
            agent_llm_config["base_url"] = provider_config["base_url"]
    
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
    
    # Get workspace path
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


def load_roles_config(config_path: Union[str, Path] = "config/roles.yaml") -> Dict[str, RoleConfig]:
    """
    Load and validate the roles configuration from YAML file.
    
    Args:
        config_path: Path to the roles configuration file
        
    Returns:
        Dictionary of role configurations, keyed by role ID
    """
    # Convert to Path if string
    if isinstance(config_path, str):
        path = Path(config_path)
    else:
        path = config_path
        
    try:
        with open(path, 'r', encoding='utf-8') as file:
            raw_config = yaml.safe_load(file)
            logger.info(f"Successfully loaded roles configuration from {path}")
            
            # Extract the roles dictionary from the config
            raw_roles = raw_config.get("roles", {}) if raw_config else {}
            
            # Convert role dictionaries to RoleConfig objects
            roles_dict = {}
            for role_key, role_data in raw_roles.items():
                try:
                    roles_dict[role_key] = RoleConfig(**role_data)
                except Exception as e:
                    logger.warning(f"Failed to validate role config for '{role_key}': {str(e)}")
                    # Skip invalid roles
                    continue
            
            return roles_dict
            
    except Exception as e:
        logger.warning(f"Failed to load roles config from {path}: {str(e)}")
        logger.warning("Using default empty configuration")
        return {}


def get_role_config(roles_config: Dict[str, RoleConfig], role_key: str) -> Optional[RoleConfig]:
    """
    Get configuration for a specific role.
    
    Args:
        roles_config: Dictionary of role configurations
        role_key: The key of the role to retrieve
        
    Returns:
        RoleConfig object or None if not found
    """
    return roles_config.get(role_key)


def get_validated_role_config(roles_config: Union[Dict[str, RoleConfig], Dict[str, Any]], role_key: str) -> Optional[RoleConfig]:
    """
    Get validated configuration for a specific role using the RoleConfig model.
    
    Args:
        roles_config: Dictionary of role configurations (either Dict[str, RoleConfig] or raw dict)
        role_key: The key of the role to retrieve
        
    Returns:
        RoleConfig object or None if the role is not found
    """
    # Handle the case where we have a Dict[str, RoleConfig]
    if role_key in roles_config and isinstance(roles_config[role_key], RoleConfig):
        return roles_config[role_key]
    
    # Handle the case where we have a raw dictionary
    if isinstance(roles_config, dict) and "roles" in roles_config:
        try:
            role_data = roles_config["roles"].get(role_key)
            if role_data:
                try:
                    # Create validated RoleConfig object
                    return RoleConfig(**role_data)
                except Exception as e:
                    logger.warning(f"Failed to validate role config for '{role_key}': {str(e)}")
        except (KeyError, TypeError, AttributeError) as e:
            logger.warning(f"Role '{role_key}' not found in configuration: {str(e)}")
    
    return None


def create_agent_config(
    role_key: str,
    name: Optional[str] = None,
    system_message: Optional[str] = None,
    llm_config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> AgentConfig:
    """
    Create an AgentConfig object for a specific role.
    
    Args:
        role_key: The key of the role this agent fulfills
        name: Optional custom name for the agent
        system_message: Optional custom system message
        llm_config: Optional LLM configuration
        **kwargs: Additional agent configuration parameters
        
    Returns:
        An AgentConfig object
    """
    # If name is not provided, use role_key as name
    if name is None:
        name = role_key.replace('_', ' ').title().replace(' ', '_')
    
    # Create agent config
    agent_config = {
        "name": name,
        "role_key": role_key,
        **kwargs
    }
    
    # Add optional parameters if provided
    if system_message is not None:
        agent_config["system_message"] = system_message
    
    if llm_config is not None:
        agent_config["llm_config"] = llm_config
    
    return AgentConfig(**agent_config)
