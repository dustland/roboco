"""
Roboco - Multi-Agent Collaboration Framework

A production-ready framework for building collaborative AI agent teams.
Built on AG2 (AutoGen) with configuration-based team setup.

Usage:
    from roboco import TeamManager, Agent, UserAgent
    
    # Direct usage
    team = TeamManager("path/to/team.yaml")
    result = await team.run("Your task here")
    
    # Configuration-based team creation
    from roboco import TeamBuilder
    
    team = TeamBuilder.create_team("config/team.yaml")
    result = await team.run("Your task here")
    
    # For task management, use the CLI module:
    from roboco.core.cli import run_task, resume_task, list_tasks
    
    result = await run_task("config/team.yaml", "Your task here")
    await resume_task(result.task_id, max_rounds=10)
"""

from typing import Optional

# Core classes - the main API
from .core import (
    TeamManager, Agent, UserAgent, CollaborationResult,
    TeamBuilder
)

# Configuration and utilities
from .config import create_prompt_loader
from .core.exceptions import ConfigurationError

# Event system
from .event import Event, InMemoryEventBus, EventMonitor, CollaborationMetrics

# Memory system
from .memory import MemoryManager

# Tool system
from .tool import Tool, ToolRegistry

# Version info
__version__ = "0.7.0"

# Main exports for easy importing
__all__ = [
    # Core classes
    "TeamManager",
    "Agent", 
    "UserAgent",
    "CollaborationResult",
    "TeamBuilder",
    
    # Configuration
    "create_prompt_loader",
    "ConfigurationError",
    
    # Event system
    "Event",
    "InMemoryEventBus",
    "EventMonitor",
    "CollaborationMetrics",
    
    # Memory system
    "MemoryManager",
    
    # Tool system
    "Tool",
    "ToolRegistry",
    
    
    # Package info
    "__version__",
]
