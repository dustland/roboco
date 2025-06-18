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
from .core.task import execute_task, start_task, TaskExecutor, Task
from .core.orchestrator import Orchestrator
from .config.team_loader import load_team_config
from .config.agent_loader import load_single_agent_config, load_agents_config

# Tool framework - new system
from .tool.registry import register_tool, get_tool_registry
from .tool.executor import ToolExecutor, ToolResult
from .tool.base import Tool, ToolFunction
from .tool.schemas import get_tool_schemas
from .tool.manager import ToolManager

# Tool framework - old system (for backward compatibility)
from .core.tool import tool, execute_tool
from .core.tool import Tool as OldTool, ToolResult as OldToolResult

# Built-in tools
from .builtin_tools import *

# Storage and memory
from .storage.factory import StorageFactory
from .memory.factory import create_memory_backend, create_default_memory_backend

# Search capabilities
from .search.search_manager import SearchManager

# Messages and data
from .core.message import TaskStep, TextPart, ToolCallPart, ToolResultPart, ToolCall, Artifact

# Configuration
from .core.config import AgentConfig, TeamConfig, BrainConfig, ToolConfig

# Prompt loading
from .config.prompt_loader import PromptLoader, create_prompt_loader

# Utilities
from .utils.logger import get_logger, configure_logging, setup_clean_chat_logging

__version__ = "0.9.0"

__all__ = [
    # Main API
    "execute_task",
    "start_task",
    "TaskExecutor",
    "Task",
    
    # Core components
    "Agent", 
    "Orchestrator",
    "Brain",
    
    # Tool framework - new system
    "Tool",
    "ToolFunction",
    "ToolResult",
    "ToolExecutor",
    "ToolManager",
    "register_tool",
    "get_tool_registry",
    "get_tool_schemas",
    
    # Tool framework - old system (backward compatibility)
    "tool",  # decorator
    "execute_tool",
    "OldTool",
    "OldToolResult",
    
    # Messages and data
    "TaskStep", 
    "TextPart",
    "ToolCallPart",
    "ToolResultPart",
    "ToolCall",
    "Artifact",
    
    # Configuration
    "AgentConfig", 
    "TeamConfig",
    "BrainConfig",
    "ToolConfig",
    "load_team_config",
    "load_single_agent_config",
    "load_agents_config", 
    "PromptLoader",
    "create_prompt_loader",
    
    # Memory system
    "create_memory_backend",
    "create_default_memory_backend",
    
    # Search system
    "SearchManager",
    
    # Logging utilities
    "get_logger",
    "configure_logging",
    "setup_clean_chat_logging",
]
