"""
Tool Factory for Roboco

This module provides a factory for creating and managing tools through automatic discovery.
It simplifies the process of registering tools with autogen's ConversableAgent instances.
"""

import importlib
import inspect
import os
import pkgutil
from typing import Dict, Any, List, Optional, Callable, Type, Union
from loguru import logger

from roboco.core.tool import Tool

# For type hints
try:
    from autogen import ConversableAgent
except ImportError:
    ConversableAgent = Any  # Type hint fallback if autogen isn't available

class ToolFactory:
    """Factory for creating and managing autogen-compatible tools through automatic discovery."""
    
    @classmethod
    def discover_tools(cls) -> Dict[str, Type]:
        """
        Discover all tool classes in the tools package.
        
        Returns:
            Dictionary mapping tool names to tool classes
        """
        from roboco import tools
        
        tool_classes = {}
        
        # Get the path to the tools package
        tools_path = os.path.dirname(tools.__file__)
        
        # Iterate through all modules in the tools package
        for _, module_name, is_pkg in pkgutil.iter_modules([tools_path]):
            # Skip __init__.py and this factory itself
            if module_name == '__init__' or module_name == 'tool_factory':
                continue
                
            try:
                # Import the module
                module = importlib.import_module(f'roboco.tools.{module_name}')
                
                # Find all classes in the module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Look for classes that appear to be tools (have public methods)
                    if cls._is_tool_class(obj):
                        # Use the class name as the tool name
                        tool_classes[name] = obj
                        logger.debug(f"Discovered tool class: {name}")
            except Exception as e:
                logger.warning(f"Error importing tool module '{module_name}': {e}")
        
        logger.info(f"Discovered {len(tool_classes)} tool classes")
        return tool_classes
    
    @staticmethod
    def _is_tool_class(cls: Type) -> bool:
        """
        Check if a class appears to be a tool (has public methods).
        
        Args:
            cls: Class to check
            
        Returns:
            True if the class is a tool, False otherwise
        """
        # Check if the class inherits from Tool
        if hasattr(cls, '__mro__'):
            for base in cls.__mro__:
                if base.__name__ == 'Tool' and base.__module__ == 'roboco.core.tool':
                    return True
        
        # As a fallback, check if the class has the methods we expect from a tool
        return (hasattr(cls, 'name') and 
                hasattr(cls, 'description') and 
                hasattr(cls, 'get_functions'))
    
    @classmethod
    def create_tool(cls, tool_name: str, **kwargs: Any) -> Any:
        """
        Create an instance of a tool by name.
        
        Args:
            tool_name: Name of the tool class to instantiate
            **kwargs: Additional parameters for tool initialization
            
        Returns:
            An instance of the requested tool
            
        Raises:
            ValueError: If the tool class is not found
        """
        tool_classes = cls.discover_tools()
        
        if tool_name not in tool_classes:
            available_tools = ", ".join(tool_classes.keys())
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {available_tools}")
            
        # Create and return the tool instance
        tool_class = tool_classes[tool_name]
        tool = tool_class(**kwargs)
        logger.info(f"Created tool instance: {tool_name}")
        return tool
    
    @classmethod
    def create_all_tools(cls, **kwargs: Any) -> Dict[str, Any]:
        """
        Create instances of all available tools.
        
        Args:
            **kwargs: Additional parameters for tool initialization
            
        Returns:
            Dictionary mapping tool names to tool instances
        """
        tool_classes = cls.discover_tools()
        tools = {}
        
        for name, tool_class in tool_classes.items():
            try:
                tools[name] = tool_class(**kwargs)
                logger.debug(f"Created tool instance: {name}")
            except Exception as e:
                logger.warning(f"Error creating tool '{name}': {e}")
                
        logger.info(f"Created {len(tools)} tool instances")
        return tools
    
    @classmethod
    def create_function_map(cls, tool_names: Optional[List[str]] = None, 
                          tool_instances: Optional[Dict[str, Any]] = None) -> Dict[str, Callable]:
        """
        Create a function map suitable for autogen's ConversableAgent.
        
        Args:
            tool_names: List of tool names to include in the function map.
                      If None and tool_instances is None, include all discovered tools.
            tool_instances: Dictionary of pre-created tool instances.
                          If provided, tool_names is ignored.
                       
        Returns:
            A dictionary mapping function names to callable functions
        """
        function_map = {}
        
        # If tool instances are provided, use them
        if tool_instances is not None:
            tools_to_process = tool_instances
        # Otherwise create the specified tools or discover all tools
        else:
            tool_classes = cls.discover_tools()
            
            # If no specific tools requested, use all discovered tools
            if tool_names is None:
                tool_names = list(tool_classes.keys())
                
            # Create the requested tools
            tools_to_process = {}
            for name in tool_names:
                if name in tool_classes:
                    try:
                        tools_to_process[name] = cls.create_tool(name)
                    except Exception as e:
                        logger.warning(f"Error creating tool '{name}': {e}")
        
        # Extract methods from all tools
        for tool_name, tool in tools_to_process.items():
            # Get all public methods from the tool
            for method_name, method in inspect.getmembers(tool, predicate=inspect.ismethod):
                if not method_name.startswith('_'):
                    # Create a function map entry with a descriptive name
                    function_key = f"{tool_name}_{method_name}"
                    function_map[function_key] = method
                    logger.debug(f"Added function to map: {function_key}")
        
        logger.info(f"Created function map with {len(function_map)} functions")
        return function_map
    
    @classmethod
    def register_tools_with_agent(cls, agent: ConversableAgent, 
                               tool_names: Optional[List[str]] = None) -> None:
        """
        Register tools with an autogen agent.
        
        Args:
            agent: The agent to register tools with
            tool_names: List of tool names to register.
                      If None, register all discovered tools.
        """
        function_map = cls.create_function_map(tool_names=tool_names)
        
        # Register the function map with the agent
        for func_name, func in function_map.items():
            agent.register_function(
                function_map={func_name: func}
            )
        
        logger.info(f"Registered {len(function_map)} functions with agent {agent.name}")
    
    @classmethod
    def get_available_tools(cls) -> List[str]:
        """
        Get a list of all discovered tool names.
        
        Returns:
            List of discovered tool names
        """
        tool_classes = cls.discover_tools()
        return list(tool_classes.keys())
