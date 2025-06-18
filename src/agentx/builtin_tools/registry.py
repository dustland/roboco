"""
Built-in tools registry for AgentX framework.

This module handles registration of all built-in tools with tool registries.
"""

def register_builtin_tools(registry, workspace_path: str = None, memory_system=None):
    """
    Register all built-in tools with a specific registry.
    
    Args:
        registry: The tool registry to register tools with
        workspace_path: Optional workspace path for storage tools
        memory_system: Optional memory system for memory tools
    """
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
    
    # Register memory tools only if memory system is available
    if memory_system:
        try:
            from .memory_tools import MemoryTool
            registry.register_tool(MemoryTool(memory_system))
        except Exception as e:
            # Memory tools are optional - don't fail if they can't be registered
            pass
    
    # Register search tools
    from .search_tools import SearchTool
    registry.register_tool(SearchTool())
    
    # Register web tools
    from .web_tools import WebTool
    registry.register_tool(WebTool()) 