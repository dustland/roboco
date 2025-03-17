"""
Tool Factory for Roboco (DEPRECATED)

This module provides a factory for creating and managing tools through automatic discovery.
It simplifies the process of registering tools with autogen's ConversableAgent instances.

DEPRECATED: Please use the Tool.register_with_agents method instead.
"""

import importlib
import inspect
import os
import pkgutil
import warnings
from typing import Dict, Any, List, Callable, Type
from loguru import logger

from roboco.core.tool import Tool


class ToolFactory:
    """
    Factory for creating and managing autogen-compatible tools through automatic discovery.
    
    DEPRECATED: Please use the Tool.register_with_agents method instead.
    """
    
    @classmethod
    def discover_tools(cls) -> Dict[str, Type]:
        """
        Discover all tool classes in the tools package.
        
        DEPRECATED: Please use the Tool.register_with_agents method instead.
        
        Returns:
            Dictionary mapping tool names to tool classes
        """
        warnings.warn(
            "ToolFactory.discover_tools is deprecated and will be removed in a future version. "
            "Please use the Tool.register_with_agents method instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
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
    def create_tool(cls, tool_name: str, **kwargs: Any) -> Tool:
        """
        Create an instance of a tool by name.
        
        DEPRECATED: Please use the Tool.register_with_agents method instead.
        
        Args:
            tool_name: Name of the tool class to instantiate
            **kwargs: Additional parameters for tool initialization
            
        Returns:
            An instance of the requested tool
            
        Raises:
            ValueError: If the tool class is not found
        """
        warnings.warn(
            "ToolFactory.create_tool is deprecated and will be removed in a future version. "
            "Please use the Tool.register_with_agents method instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
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
        
        DEPRECATED: Please use the Tool.register_with_agents method instead.
        
        This follows AG2's pattern of having a caller agent (that suggests the tool)
        and an executor agent (that executes the tool).
        
        Args:
            caller_agent: The agent that will suggest using the tool
            executor_agent: The agent that will execute the tool
            tool_name: Name of the tool to register
            **kwargs: Additional parameters for tool initialization
        """
        warnings.warn(
            "ToolFactory.register_tool is deprecated and will be removed in a future version. "
            "Please use the Tool.register_with_agents method instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        # Create the tool instance
        tool = cls.create_tool(tool_name, **kwargs)
        
        # Use the tool's register_with_agents method
        tool.register_with_agents(caller_agent, executor_agent)
    
    @classmethod
    def get_available_tools(cls) -> List[str]:
        """
        Get a list of all discovered tool names.
        
        DEPRECATED: Please use the Tool.register_with_agents method instead.
        
        Returns:
            List of discovered tool names
        """
        warnings.warn(
            "ToolFactory.get_available_tools is deprecated and will be removed in a future version. "
            "Please use the Tool.register_with_agents method instead.",
            DeprecationWarning,
            stacklevel=2
        )
        
        tool_classes = cls.discover_tools()
        return list(tool_classes.keys())
