"""
Core module for the roboco framework.

This module provides the core functionality for the roboco framework,
including the agent, team, task, and project management.
"""

# Basic components with no circular dependencies
from roboco.core.agent import Agent
from roboco.core.team import Team
from roboco.core.agent_factory import AgentFactory
from roboco.core.tool import Tool, command
from roboco.core.config import load_config, save_config, create_default_config, get_llm_config, load_roles_config, get_role_config, get_validated_role_config, create_agent_config
from roboco.core.fs import ProjectFS, ProjectNotFoundError, get_project_fs
from roboco.core.project_manager import ProjectManager

# Models
from roboco.core.models import Task, RobocoConfig, LLMConfig, ToolConfig, TeamConfig

# Logging
from loguru import logger
from roboco.core.logger import configure_logger, enable_file_logging, disable_file_logging, reset_logger, load_config_settings

# These managers are included last to avoid circular imports
from roboco.core.task_manager import TaskManager
from roboco.core.team_manager import TeamManager
from roboco.core.mcp_agent import McpAgent

__all__ = [
    # Core classes
    "Agent",
    "Team",
    "AgentFactory",
    "Tool",
    "command",
    "Task",
    "ProjectManager",
    "RobocoConfig",
    "LLMConfig",
    "ToolConfig",
    "TeamConfig",
    
    # Managers
    "TaskManager",
    "TeamManager", 
    
    # Filesystem
    "ProjectFS",
    "ProjectNotFoundError",
    "get_project_fs",
    
    # Configuration
    "load_config",
    "save_config",
    "create_default_config",
    "get_llm_config",
    "load_roles_config",
    "get_role_config",
    "get_validated_role_config",
    "create_agent_config",
    
    # Logging
    "logger",
    "configure_logger",
    "enable_file_logging",
    "disable_file_logging",
    "reset_logger",
    "load_config_settings",
    
    # New additions
    "McpAgent"
]

# NOTE: load_config_settings() should be called explicitly by the application entry point
# to avoid circular imports. DO NOT call it here.
# See examples/app_example.py for the correct usage pattern.