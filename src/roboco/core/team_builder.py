"""
Team Builder Implementation

Implements the configuration-based team creation system as described in the design documents.
Supports Jinja2 template rendering, role definitions, and dynamic team composition.
"""

import os
import yaml
import importlib
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from .team_manager import TeamManager
from ..config import create_prompt_loader
from ..config.models import MemoryConfig, EventConfig
from ..core.exceptions import ConfigurationError
from ..memory.manager import MemoryManager
from ..event import InMemoryEventBus


class TeamBuilder:
    """
    Utility for building teams from configuration files using Jinja2 templates.
    Implements the configuration-based design pattern described in the documentation.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the TeamBuilder.
        
        Args:
            config_dir: Base configuration directory. Defaults to './config'
        """
        self.config_dir = Path(config_dir or "./config")
        
        # Look for templates in multiple possible directories
        template_dirs = [
            self.config_dir / "prompts", 
            self.config_dir / "templates"
        ]
        
        self.template_dir = None
        for template_dir in template_dirs:
            if template_dir.exists():
                self.template_dir = template_dir
                break
        
        # Set up Jinja2 environment for template rendering
        if self.template_dir:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=False  # We're generating prompts, not HTML
            )
        else:
            self.jinja_env = None
    
    @staticmethod
    def create_team(config_path: Optional[str] = None, 
                   template_variables: Optional[Dict[str, Any]] = None,
                   memory_config: Optional[MemoryConfig] = None,
                   event_config: Optional[EventConfig] = None,
                   event_bus=None,
                   task_id: Optional[str] = None) -> TeamManager:
        """
        Create a team from configuration files.
        
        Args:
            config_path: Path to team configuration YAML file. Defaults to './config/default.yaml'
            template_variables: Variables to use in Jinja2 template rendering
            memory_config: Memory system configuration
            event_config: Event system configuration
            event_bus: Optional event bus instance to use
            task_id: Optional existing task ID for continuation
            
        Returns:
            Configured TeamManager instance
        """
        if config_path is None:
            config_path = "./config/default.yaml"
        
        # For the new simplified structure, just create TeamManager directly
        return TeamManager(config_path=config_path, event_bus=event_bus, task_id=task_id)
    
    @staticmethod
    def create_team_from_preset(preset_name: str,
                               template_variables: Optional[Dict[str, Any]] = None,
                               **kwargs) -> TeamManager:
        """
        Create a team from a preset configuration.
        
        Args:
            preset_name: Name of the preset (e.g., "superwriter", "simple_team")
            template_variables: Variables for template rendering
            **kwargs: Additional arguments passed to create_team
            
        Returns:
            Configured TeamManager instance
        """
        # Try to find preset in multiple locations
        preset_paths = [
            f"./config/presets/{preset_name}.yaml",
            f"./examples/{preset_name}/config/default.yaml",
            f"./presets/{preset_name}/default.yaml"
        ]
        
        config_path = None
        for path in preset_paths:
            if Path(path).exists():
                config_path = path
                break
        
        if not config_path:
            raise ConfigurationError(
                f"Preset '{preset_name}' not found. Searched in: {preset_paths}"
            )
        
        return TeamBuilder.create_team(
            config_path=config_path,
            template_variables=template_variables,
            **kwargs
        )


# Convenience functions for preset teams
def create_planning_team(template_variables: Optional[Dict[str, Any]] = None,
                        **kwargs) -> TeamManager:
    """Create a planning-focused team."""
    return TeamBuilder.create_team_from_preset(
        "simple_team",
        template_variables=template_variables,
        **kwargs
    )

def create_research_writing_team(template_variables: Optional[Dict[str, Any]] = None,
                                **kwargs) -> TeamManager:
    """Create a research and writing team."""
    return TeamBuilder.create_team_from_preset(
        "superwriter", 
        template_variables=template_variables,
        **kwargs
    )

def create_software_development_team(template_variables: Optional[Dict[str, Any]] = None,
                                   **kwargs) -> TeamManager:
    """Create a software development team."""
    return TeamBuilder.create_team_from_preset(
        "simple_team", 
        template_variables=template_variables,
        **kwargs
    ) 