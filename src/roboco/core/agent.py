"""
Base Agent Module

This module defines the base Agent class that extends AG2's AssistantAgent.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from loguru import logger

# ag2 and autogen are identical packages
from autogen import AssistantAgent, ConversableAgent
from roboco.core.tool_factory import ToolFactory
from roboco.core.config import load_config, get_llm_config

class Agent(ConversableAgent):
    """Base agent class that all roboco agents inherit from."""

    def __init__(
        self,
        name: str,
        system_message: str,
        _tools: Optional[List[Any]] = None,
        config_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize an agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            _tools: Optional list of tools available to the agent
            config_path: Optional path to agent configuration file
            **kwargs: Additional arguments passed to ConversableAgent
        """
        # Load configuration
        config = load_config(config_path)
        llm_config = get_llm_config(config)
        
        # Initialize base class
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            **kwargs
        )
        
        # Store tools
        self._tools = _tools or []
        
        logger.info(f"Initialized Agent: {name}")
        if self._tools:
            logger.info(f"Agent has {len(self._tools)} tools available")
    
    def register_tool(self, tool) -> None:
        """
        Register a tool with the agent.
        
        Args:
            tool: The tool to register
        """
        if hasattr(tool, "get_functions"):
            functions = tool.get_functions()
            self.register_function(function_map=functions)
            logger.info(f"Registered {len(functions)} functions from tool {tool.__class__.__name__}")
        else:
            logger.warning(f"Tool {tool.__class__.__name__} does not have a get_functions method")