"""
Tool Factory for AG2 Integration

This module provides a factory for creating and managing tools that are compatible with the AG2 framework.
It simplifies the process of registering tools with AG2's ConversableAgent instances.
"""

from typing import Dict, Any, List, Optional, Callable, Type
import inspect
from loguru import logger

class ToolFactory:
    """Factory for creating and managing AG2-compatible tools."""
    
    def __init__(self):
        """Initialize the tool factory."""
        self.tools = {}
        
    def register_tool(self, name: str, tool_class: Type, **kwargs) -> None:
        """
        Register a tool with the factory.
        
        Args:
            name: Name of the tool
            tool_class: Class of the tool
            **kwargs: Additional parameters for tool initialization
        """
        self.tools[name] = {
            "class": tool_class,
            "params": kwargs
        }
        logger.info(f"Registered tool: {name}")
    
    def create_tool(self, name: str, **kwargs) -> Any:
        """
        Create an instance of a registered tool.
        
        Args:
            name: Name of the registered tool
            **kwargs: Additional parameters to override defaults
            
        Returns:
            An instance of the requested tool
        """
        if name not in self.tools:
            raise ValueError(f"Tool '{name}' is not registered")
        
        tool_info = self.tools[name]
        tool_class = tool_info["class"]
        
        # Combine default params with overridden params
        params = {**tool_info["params"], **kwargs}
        
        # Create and return the tool instance
        tool = tool_class(**params)
        return tool
    
    def create_function_map(self, tool_names: List[str] = None) -> Dict[str, Callable]:
        """
        Create a function map suitable for AG2's ConversableAgent.
        
        Args:
            tool_names: List of tool names to include in the function map.
                       If None, include all registered tools.
                       
        Returns:
            A dictionary mapping function names to callable functions
        """
        function_map = {}
        
        # If no specific tools requested, use all registered tools
        if tool_names is None:
            tool_names = list(self.tools.keys())
        
        # Create each requested tool and extract its methods
        for name in tool_names:
            tool = self.create_tool(name)
            
            # Get all public methods from the tool
            for method_name, method in inspect.getmembers(tool, predicate=inspect.ismethod):
                if not method_name.startswith('_'):
                    # Create a function map entry with a descriptive name
                    function_key = f"{name}_{method_name}"
                    function_map[function_key] = method
                    
        return function_map
    
    def get_available_tools(self) -> List[str]:
        """
        Get a list of all registered tool names.
        
        Returns:
            List of registered tool names
        """
        return list(self.tools.keys())
