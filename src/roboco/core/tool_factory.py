"""
Tool Factory for Roboco

This module provides a factory for creating and managing tools through automatic discovery.
It simplifies the process of registering tools with autogen's ConversableAgent instances.
"""

import importlib
import inspect
import os
import pkgutil
import functools
from typing import Dict, Any, List, Optional, Callable, Type
from loguru import logger

from roboco.core.tool import Tool

class ToolFactory:
    """Factory for creating and managing autogen-compatible tools through automatic discovery."""
    
    @classmethod
    def discover_tools(cls) -> Dict[str, Type]:
        """
        Discover all tool classes in the tools package.
        
        Returns:
            Dictionary mapping tool names to tool classes
        """
        tool_classes = {}
        
        try:
            # Find the tools directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))  # core directory
            parent_dir = os.path.dirname(current_dir)  # roboco directory
            tools_path = os.path.join(parent_dir, 'tools')
            
            if not os.path.isdir(tools_path):
                logger.warning(f"Tools directory not found at {tools_path}")
                return tool_classes
            
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
                        # Look for classes that inherit from Tool
                        if issubclass(obj, Tool) and obj != Tool:
                            # Use the class name as the tool name
                            tool_classes[name] = obj
                except Exception as e:
                    logger.warning(f"Error importing tool module '{module_name}': {e}")
        except Exception as e:
            logger.error(f"Error in tool discovery process: {e}")
        
        logger.info(f"Discovered {len(tool_classes)} tool classes")
        return tool_classes
    
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
    def register_tool(cls, caller_agent: Any, executor_agent: Any, 
                      tool_name: str, **kwargs) -> None:
        """
        Register a tool with a caller agent and an executor agent.
        
        This follows AG2's pattern of having a caller agent (that suggests the tool)
        and an executor agent (that executes the tool).
        
        Args:
            caller_agent: The agent that will suggest using the tool
            executor_agent: The agent that will execute the tool
            tool_name: Name of the tool to register
            **kwargs: Additional parameters for tool initialization
        """
        # Create the tool instance
        tool = cls.create_tool(tool_name, **kwargs)
        
        # Register each public method of the tool with both agents
        for method_name in dir(tool):
            # Skip private methods and attributes
            if method_name.startswith('_') or method_name in ['name', 'description', 'get_function_definitions']:
                continue
                
            method = getattr(tool, method_name)
            if callable(method):
                # Get the method's docstring for description
                description = method.__doc__ or f"Method {method_name} from {tool_name}"
                
                # Create a standalone function that calls the method
                def make_function(tool_instance, method_name):
                    method_ref = getattr(tool_instance, method_name)
                    
                    def function(*args, **kwargs):
                        result = method_ref(*args, **kwargs)
                        # Convert result to string to ensure compatibility
                        return str(result) if result is not None else None
                    
                    # Set function metadata
                    function.__name__ = method_name
                    function.__doc__ = description
                    
                    return function
                
                # Create the standalone function
                function = make_function(tool, method_name)
                
                # Register the function with both agents
                try:
                    # Register with caller agent
                    caller_agent.register_function(
                        {method_name: function}
                    )
                    
                    # Register with executor agent
                    executor_agent.register_function(
                        {method_name: function}
                    )
                    
                    logger.debug(f"Registered method {method_name} from tool {tool_name}")
                except Exception as e:
                    logger.error(f"Error registering method {method_name}: {e}")
        
        logger.info(f"Registered methods from tool {tool_name}")
    
    @classmethod
    def get_available_tools(cls) -> List[str]:
        """
        Get a list of all discovered tool names.
        
        Returns:
            List of discovered tool names
        """
        tool_classes = cls.discover_tools()
        return list(tool_classes.keys())
