"""
Configuration Module

This module provides functionality for loading and accessing configuration settings
from the TOML configuration file.
"""

import os
import tomli
from pathlib import Path
from typing import Any, Dict, Optional, Union
import re
from loguru import logger

class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass

class Config:
    """
    Configuration manager for the Roboco system.
    
    This class handles loading configuration from TOML files and provides
    access to configuration values with environment variable interpolation.
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file. If None, will look in standard locations.
        """
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[Path] = Path(config_path) if config_path else None
        self._loaded = False
    
    def load(self) -> 'Config':
        """
        Load the configuration from the TOML file.
        
        Returns:
            Self for method chaining
            
        Raises:
            ConfigurationError: If the configuration file cannot be found or parsed
        """
        # Try to find the configuration file if not specified
        if not self._config_path:
            search_paths = [
                Path("config/config.toml"),
                Path("./config.toml"),
                Path(os.path.expanduser("~/.config/roboco/config.toml")),
                Path("/etc/roboco/config.toml"),
            ]
            
            for path in search_paths:
                if path.exists():
                    self._config_path = path
                    break
        
        if not self._config_path or not self._config_path.exists():
            raise ConfigurationError(
                "Configuration file not found. Please create a config.toml file "
                "by copying config.example.toml and modifying it as needed."
            )
        
        # Load the configuration file
        try:
            with open(self._config_path, "rb") as f:
                self._config = tomli.load(f)
            
            # Interpolate environment variables
            self._interpolate_env_vars(self._config)
            
            self._loaded = True
            logger.info(f"Loaded configuration from {self._config_path}")
            return self
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def _interpolate_env_vars(self, config_section: Dict[str, Any]) -> None:
        """
        Recursively interpolate environment variables in the configuration.
        
        Environment variables are specified as ${VAR_NAME} and will be replaced
        with their values from the environment.
        
        Args:
            config_section: The configuration section to process
        """
        env_var_pattern = re.compile(r'\${([A-Za-z0-9_]+)}')
        
        for key, value in config_section.items():
            if isinstance(value, dict):
                self._interpolate_env_vars(value)
            elif isinstance(value, str):
                # Replace environment variables
                matches = env_var_pattern.findall(value)
                for match in matches:
                    env_value = os.environ.get(match)
                    if env_value is not None:
                        value = value.replace(f"${{{match}}}", env_value)
                
                config_section[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by its key path.
        
        Args:
            key_path: Dot-separated path to the configuration value (e.g., "llm.model")
            default: Default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        if not self._loaded:
            self.load()
        
        # Split the key path and navigate through the configuration
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_section(self, section_path: str) -> Dict[str, Any]:
        """
        Get an entire configuration section.
        
        Args:
            section_path: Dot-separated path to the configuration section (e.g., "llm")
            
        Returns:
            The configuration section as a dictionary
            
        Raises:
            ConfigurationError: If the section is not found
        """
        section = self.get(section_path)
        if not isinstance(section, dict):
            raise ConfigurationError(f"Configuration section '{section_path}' not found")
        
        return section
    
    @property
    def config_path(self) -> Optional[Path]:
        """Get the path to the loaded configuration file."""
        return self._config_path

# Create a singleton instance
config = Config() 