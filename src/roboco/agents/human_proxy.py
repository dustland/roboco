"""
Human Proxy Agent Module

This module defines the HumanProxy agent that extends roboco's Agent class
for human-in-the-loop interactions.
"""

from typing import Dict, Any, Optional, Callable
from loguru import logger

from autogen import register_function
from roboco.core.agent import Agent
from roboco.core.config import load_config, get_llm_config

class HumanProxy(Agent):
    """Human proxy agent class that integrates with roboco's configuration system.
    
    This class extends roboco's Agent class to provide human-in-the-loop functionality.
    It is designed to interact directly with users and execute tools.
    """
    
    def __init__(
        self,
        name: str,
        system_message: str = "You are a human user interacting with AI assistants.",
        config_path: Optional[str] = None,
        human_input_mode: str = "NEVER",
        code_execution_config: Optional[Dict[str, Any]] = None,
        llm_model: str = "gpt-4o",
        terminate_msg: str = "TERMINATE",
        **kwargs
    ):
        """Initialize a human proxy agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            config_path: Optional path to agent configuration file
            human_input_mode: Mode for human input (ALWAYS, TERMINATE, NEVER)
            code_execution_config: Configuration for code execution
            llm_model: The LLM model to use (e.g., "gpt-4o", "claude-3-7-sonnet-20250219")
            terminate_msg: Message to check for termination
            **kwargs: Additional arguments passed to Agent
        """
        # Setup code execution config if provided
        if code_execution_config is None:
            code_execution_config = {"work_dir": "workspace", "use_docker": False}
        else:
            # Ensure use_docker is set to False
            code_execution_config["use_docker"] = False
        
        # Initialize base Agent class
        super().__init__(
            name=name,
            system_message=system_message,
            config_path=config_path,
            llm_model=llm_model,
            human_input_mode=human_input_mode,
            check_terminate_msg=terminate_msg,
            code_execution_config=code_execution_config,
            **kwargs
        )
        
        logger.info(f"Initialized HumanProxy: {name}")
        
    def register_tool(self, function: Callable, description: str = None) -> None:
        """
        Register a tool with this human proxy agent as the executor.
        
        This simplifies the process of registering tools that will be executed by a human proxy.
        
        Args:
            function: The function to register as a tool
            description: Optional description of the tool
        """
        # Ensure description is a string, not a boolean
        if description is None:
            description = f"Function {function.__name__} provided by {self.name}"
        elif not isinstance(description, str):
            description = str(description)
            
        register_function(
            function,
            executor=self,
            description=description
        )
        logger.info(f"Registered function {function.__name__} with executor {self.name}")
