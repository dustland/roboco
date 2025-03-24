"""
Human Proxy Agent Module

This module defines the HumanProxy agent that extends AG2's UserProxyAgent
for human-in-the-loop interactions.
"""

from typing import Dict, Any, Optional, Callable
from loguru import logger

from autogen import UserProxyAgent, register_function
from roboco.core.config import load_config, get_llm_config

class HumanProxy(UserProxyAgent):
    """Human proxy agent class that integrates with roboco's configuration system.
    
    This class extends AG2's UserProxyAgent to provide additional functionality:
    1. Integration with roboco's configuration system
    2. Tool management
    
    This is specifically designed for human-in-the-loop interactions.
    """
    
    def __init__(
        self,
        name: str,
        system_message: str = "You are a human user interacting with AI assistants.",
        config_path: Optional[str] = None,
        human_input_mode: str = "NEVER",
        code_execution_config: Optional[Dict[str, Any]] = None,
        llm_provider: str = "llm",
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
            llm_provider: The LLM provider to use (e.g., "llm", "openai", "deepseek", "ollama")
            **kwargs: Additional arguments passed to UserProxyAgent
        """
        # Use provided configuration or load from config if None
        if 'llm_config' not in kwargs:
            config = load_config(config_path)
            llm_config = get_llm_config(config, provider=llm_provider)
            logger.debug(f"Loaded llm_config for {name} using provider {llm_provider}: {llm_config}")
        
        # Setup code execution config if provided
        if code_execution_config is None:
            code_execution_config = {"work_dir": "workspace", "use_docker": False}
        else:
            # Ensure use_docker is set to False
            code_execution_config["use_docker"] = False
        
        # Initialize base UserProxyAgent class
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=human_input_mode,
            is_termination_msg=lambda x: terminate_msg in (x.get("content", "") or ""),
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
        register_function(
            function,
            executor=self,
            description=description
        )
        logger.info(f"Registered function {function.__name__} with executor {self.name}")
