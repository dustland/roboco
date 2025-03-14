"""
Base Agent Module

This module defines the base Agent class that extends AG2's AssistantAgent.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from loguru import logger

# Import directly from autogen
from autogen import AssistantAgent, ConversableAgent

class Agent(AssistantAgent):
    """Base class for all roboco agents, extending AG2's AssistantAgent."""
    
    def __init__(
        self, 
        name: str, 
        system_message: str, 
        llm_config: Dict[str, Any],
        function_map: Optional[Dict[str, Callable]] = None,
        human_input_mode: str = "NEVER"
    ):
        """
        Initialize the agent by extending AG2's AssistantAgent.
        
        Args:
            name: The name of the agent
            system_message: The system message that defines the agent's role and behavior
            llm_config: Configuration for the language model
            function_map: Dictionary mapping function names to callable functions
            human_input_mode: When to request human input
        """
        # Initialize the parent AssistantAgent
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            function_map=function_map or {},
            human_input_mode=human_input_mode
        )
        
        logger.info(f"Initialized Agent: {name}")
    
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