"""
Base Agent Module

This module defines the Agent class that extends AG2's AssistantAgent,
and HumanProxy that extends AG2's UserProxyAgent.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from loguru import logger

# ag2 and autogen are identical packages
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, register_function
from roboco.core.config import load_config, get_llm_config

class Agent(AssistantAgent):
    """Base agent class that all roboco assistant agents inherit from.
    
    This class extends AG2's AssistantAgent to provide additional functionality:
    1. Integration with roboco's configuration system
    2. Standardized termination message handling
    3. Tool management
    
    The termination message feature allows agents to signal when they have completed
    their response, following AG2's conversation termination pattern. When an agent
    includes the termination message in its response, other agents can recognize it
    and end the conversation.
    
    The termination message is:
    1. Configurable through the config file
    2. Automatically appended to the system message
    3. Propagated to other agents during conversation
    """

    def __init__(
        self,
        name: str,
        system_message: str,
        config_path: Optional[str] = None,
        terminate_msg: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize an agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            config_path: Optional path to agent configuration file
            terminate_msg: Optional message to include at the end of responses to signal completion.
                           If None, uses the value from config.
            llm_config: Optional LLM configuration. If None, loads from config_path.
            **kwargs: Additional arguments passed to AssistantAgent
        """
        # Use provided llm_config or load from config if None
        if llm_config is None and 'llm_config' not in kwargs:
            config = load_config(config_path)
            llm_config = get_llm_config(config)
            logger.debug(f"Loaded llm_config for {name}: {llm_config}")
        else:
            logger.debug(f"Using provided llm_config for {name}")
        
        # Store termination message
        self.terminate_msg = terminate_msg
        
        # Append termination instructions to system message if a termination message is provided
        if terminate_msg:
            system_message = f"{system_message}\n\nWhen you have completed your response, end your message with \"{terminate_msg}\" to signal that you are done."
        
        # Initialize base class
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            **kwargs
        )
        
        logger.info(f"Initialized Agent: {name}")
    
    def register_tool(self, function: Callable, executor_agent: ConversableAgent, description: str = None) -> None:
        """
        Register a tool with this agent as the caller and another agent as the executor.
        
        This follows AG2's pattern of having a caller agent (that suggests the tool)
        and an executor agent (that executes the tool).
        
        Args:
            function: The function to register as a tool
            executor_agent: The agent that will execute the tool
            description: Optional description of the tool for the LLM
        """
        register_function(
            function,
            caller=self,
            executor=executor_agent,
            description=description
        )
        logger.info(f"Registered function {function.__name__} with caller {self.name} and executor {executor_agent.name}")


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
        **kwargs
    ):
        """Initialize a human proxy agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            config_path: Optional path to agent configuration file
            human_input_mode: Mode for human input (ALWAYS, TERMINATE, NEVER)
            code_execution_config: Configuration for code execution
            **kwargs: Additional arguments passed to UserProxyAgent
        """
        # Use provided configuration or load from config if None
        if 'llm_config' not in kwargs:
            config = load_config(config_path)
            llm_config = get_llm_config(config)
            logger.debug(f"Loaded llm_config for {name}: {llm_config}")
        
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