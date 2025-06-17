"""
Built-in tools for AgentX framework.

This module provides essential tools that are commonly needed across different agent types:
- Storage and artifact management
- Context and planning tools
- Search and web tools
- Memory operations
"""

from .storage_tools import *
from .context_tools import *
from .planning_tools import *
from .memory_tools import *
from .search_tools import *
from .web_tools import *

def register_builtin_tools(workspace_path: str = None):
    """
    Register all built-in tools with the global registry.
    
    Args:
        workspace_path: Optional workspace path for storage tools
    """
    from ..tool.registry import get_tool_registry
    
    registry = get_tool_registry()
    
    # Register storage tools if workspace provided
    if workspace_path:
        from .storage_tools import create_storage_tools
        storage_tools = create_storage_tools(workspace_path)
        for tool in storage_tools:
            registry.register_tool(tool)
    
    # Register context tools
    from .context_tools import ContextTool
    registry.register_tool(ContextTool())
    
    # Register planning tools
    from .planning_tools import PlanningTool
    registry.register_tool(PlanningTool())
    
    # Register memory tools
    from .memory_tools import MemoryTool
    registry.register_tool(MemoryTool())
    
    # Register search tools
    from .search_tools import SearchTool
    registry.register_tool(SearchTool())
    
    # Register web tools
    from .web_tools import WebTool
    registry.register_tool(WebTool())


# Export tool classes for direct use if needed
__all__ = [
    "ContextTool", 
    "PlanningTool",
    "MemoryTool",
    "SearchTool",
    "WebTool",
    "register_builtin_tools"
] 