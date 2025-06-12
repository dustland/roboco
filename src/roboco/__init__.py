"""
Roboco - Multi-Agent Collaboration Framework

A production-ready framework for building collaborative AI agent teams.
Built on AG2 (AutoGen) with configuration-based team setup.

Usage:
    from roboco import TeamManager, Agent, ToolExecutorAgent
    
    # Simple usage
    team = TeamManager("path/to/team.yaml")
    result = await team.run("Your task here")
    
    # Or use convenience function
    from roboco import create_team, run_team
    
    result = await run_team("path/to/team.yaml", "Your task here")
    
    # Configuration-based team creation
    from roboco import TeamBuilder
    
    team = TeamBuilder.create_team("config/team.yaml")
    result = await team.run("Your task here")
"""

# Core classes - the main API
from .core import (
    TeamManager, Agent, ToolExecutorAgent, CollaborationResult,
    TeamBuilder, create_planning_team, create_research_writing_team, 
    create_software_development_team
)

# Configuration and utilities
from .config import create_prompt_loader
from .core.exceptions import ConfigurationError

# Event system
from .event import Event, InMemoryEventBus

# Memory system
from .memory import MemoryManager, ContextStore, InMemoryContextStore

# Tool system
from .tool import AbstractTool, InMemoryToolRegistry

# Server components (optional)
from .server import SessionManager, Session, create_app, SessionConfig

# Convenience functions for simple usage
async def create_team(config_path: str, **kwargs) -> TeamManager:
    """
    Create a team from configuration file.
    
    Args:
        config_path: Path to team configuration YAML file
        **kwargs: Additional arguments passed to TeamManager
        
    Returns:
        Initialized TeamManager instance
        
    Example:
        team = await create_team("config/team.yaml")
        result = await team.run("Write a report on AI")
    """
    return TeamBuilder.create_team(config_path, **kwargs)

async def run_team(config_path: str, task: str, **kwargs) -> CollaborationResult:
    """
    One-shot team execution function for simple usage.
    
    Args:
        config_path: Path to team configuration YAML file
        task: Task description for the team to work on
        **kwargs: Additional arguments passed to TeamManager
        
    Returns:
        CollaborationResult with the team's output
        
    Example:
        result = await run_team("config/team.yaml", "Write a blog post about robots")
        print(result.summary)
    """
    team = TeamBuilder.create_team(config_path, **kwargs)
    return await team.run(task)

# Version info - updated to match pyproject.toml
__version__ = "0.7.0"

# Main exports for easy importing
__all__ = [
    # Core classes
    "TeamManager",
    "Agent", 
    "ToolExecutorAgent",
    "CollaborationResult",
    "TeamBuilder",
    
    # Configuration
    "create_prompt_loader",
    "ConfigurationError",
    
    # Event system
    "Event",
    "InMemoryEventBus",
    
    # Memory system
    "MemoryManager",
    "ContextStore", 
    "InMemoryContextStore",
    
    # Tool system
    "AbstractTool",
    "InMemoryToolRegistry",
    
    # Server components
    "SessionManager",
    "Session",
    "create_app",
    "SessionConfig",
    
    # Convenience functions
    "create_team",
    "run_team",
    "create_planning_team",
    "create_research_writing_team",
    "create_software_development_team",
    
    # Package info
    "__version__",
]
