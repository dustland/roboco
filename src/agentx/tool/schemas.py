"""
Tool schema utilities for generating OpenAI function calling schemas.
"""

from typing import List, Dict, Any, Optional
from .registry import get_tool_registry


def get_tool_schemas(tool_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Get tool schemas for OpenAI function calling.
    
    Args:
        tool_names: Optional list of specific tool names to get schemas for.
                   If None, returns schemas for all registered tools.
                   
    Returns:
        List of tool schemas in OpenAI function calling format
    """
    registry = get_tool_registry()
    return registry.get_tool_schemas(tool_names) 