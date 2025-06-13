"""
Roboco Tool System - Simple and Clean

A straightforward tool system with a base class and registry.
All tools (built-in or custom) use the same pattern.
"""

import inspect
import time
from typing import Dict, Any, Callable, List
from functools import wraps

def tool(name: str, description: str):
    """Decorator to mark methods as tool functions.
    
    Args:
        name: Unique identifier for the tool function
        description: Human-readable description for LLM understanding
    """
    def decorator(func):
        func._tool_name = name
        func._tool_description = description
        func._is_tool = True
        return func
    return decorator

class Tool:
    """Base class for all tools (built-in and custom).
    
    Uses reflection to discover @tool decorated methods and
    automatically generates AG2-compatible wrapper functions.
    """
    
    def __init__(self, **config):
        self.config = config
        self._discovered_tools = None
    
    def discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """Automatically discover all @tool decorated methods.
        
        Returns:
            Dictionary mapping tool names to their metadata and methods
        """
        if self._discovered_tools is not None:
            return self._discovered_tools
            
        tools = {}
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if hasattr(method, '_is_tool'):
                tools[method._tool_name] = {
                    'method': method,
                    'name': method._tool_name,
                    'description': method._tool_description,
                    'signature': inspect.signature(method)
                }
        
        self._discovered_tools = tools
        return tools
    
    def create_ag2_functions(self) -> Dict[str, Callable]:
        """Create AG2-compatible functions for all discovered tools.
        
        Returns:
            Dictionary mapping tool names to AG2-compatible wrapper functions
        """
        tools = self.discover_tools()
        ag2_functions = {}
        
        for tool_name, tool_info in tools.items():
            ag2_functions[tool_name] = self._create_ag2_function(tool_info)
        
        return ag2_functions
    
    def _create_ag2_function(self, tool_info: Dict[str, Any]) -> Callable:
        """Create a single AG2-compatible wrapper function."""
        method = tool_info['method']
        tool_name = tool_info['name']
        
        @wraps(method)
        async def ag2_wrapper(*args, **kwargs):
            try:
                # Extract context parameters
                task_id = kwargs.pop('task_id', None)
                agent_id = kwargs.pop('agent_id', None)
                
                # Delegate to original method
                result = await method(task_id, agent_id, *args, **kwargs)
                return result
                
            except Exception as e:
                raise
        
        # Preserve original annotations for AG2 type checking
        ag2_wrapper.__annotations__ = method.__annotations__.copy()
        
        return ag2_wrapper

class ToolRegistry:
    """Simple registry for all tools (built-in and custom)."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
    
    def register(self, name: str, tool_instance: Tool):
        """Register a tool instance.
        
        Args:
            name: Tool name/identifier
            tool_instance: Configured tool instance
        """
        self.tools[name] = tool_instance
        discovered = tool_instance.discover_tools()
        print(f"📦 Registered tool '{name}' with {len(discovered)} functions")
    
    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def list(self) -> List[str]:
        """List all registered tool names."""
        return list(self.tools.keys())
    
    def get_functions_for_tools(self, tool_names: List[str]) -> Dict[str, Callable]:
        """Get AG2 functions for specified tools.
        
        Args:
            tool_names: List of tool names to include
            
        Returns:
            Dictionary mapping function names to AG2-compatible callables
        """
        all_functions = {}
        
        for tool_name in tool_names:
            tool = self.get(tool_name)
            if tool:
                functions = tool.create_ag2_functions()
                all_functions.update(functions)
            else:
                print(f"⚠️ Tool '{tool_name}' not found in registry")
        
        return all_functions 