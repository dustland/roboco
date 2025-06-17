"""
AgentX - Multi-Agent Conversation Framework

A flexible framework for building AI agent teams with:
- Autonomous agents with private LLM interactions
- Centralized tool execution for security and monitoring  
- Built-in storage, memory, and search capabilities
- Team coordination and task management
"""

from .core.agent import Agent, create_assistant_agent
from .core.brain import Brain
from .core.team import Team
from .core.task import Task, create_task, execute_task, start_task
from .core.orchestrator import Orchestrator, get_orchestrator
from .config.team_loader import load_team_config
from .config.agent_loader import load_agent_config

# Tool framework
from .tool.registry import register_tool, get_tool_registry
from .tool.executor import ToolExecutor, ToolResult
from .tool.base import Tool, ToolFunction
from .tool.schemas import get_tool_schemas

# Built-in tools
from .builtin_tools import *

# Storage and memory
from .storage.factory import StorageFactory
from .memory.factory import MemoryFactory

# Search capabilities
from .search.search_manager import SearchManager

# Utilities
from .utils.logger import get_logger

__version__ = "0.1.0"

__all__ = [
    # Core components
    "Agent",
    "Brain", 
    "Team",
    "Task",
    "Orchestrator",
    "create_assistant_agent",
    "create_task",
    "execute_task",
    "start_task",
    "get_orchestrator",
    
    # Configuration
    "load_team_config",
    "load_agent_config",
    
    # Tool framework
    "Tool",
    "ToolFunction", 
    "ToolExecutor",
    "ToolResult",
    "register_tool",
    "get_tool_registry",
    "get_tool_schemas",
    
    # Factories
    "StorageFactory",
    "MemoryFactory",
    "SearchManager",
    
    # Utilities
    "get_logger",
]
