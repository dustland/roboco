"""
Base Agent Module

This module defines the Agent class that extends AG2's AssistantAgent.
"""

from typing import Dict, Any, List, Optional, Callable, Union
from loguru import logger

# ag2 and autogen are identical packages
from autogen import AssistantAgent, UserProxyAgent, ConversableAgent, register_function
from roboco.core.config import load_config, get_llm_config

# Get a logger instance for this module
logger = logger.bind(module=__name__)

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
        llm_provider: str = "llm",
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
            llm_provider: The LLM provider to use (e.g., "llm", "openai", "deepseek", "ollama").
                         This allows different agents to use different LLM providers.
            **kwargs: Additional arguments passed to AssistantAgent
        """
        # Extract llm_config from kwargs if provided
        kwargs_llm_config = kwargs.pop('llm_config', None)
        
        # Prepare the LLM configuration using the internal method
        final_provider, final_llm_config = self._prepare_llm_config(
            name=name,
            config_path=config_path,
            llm_config=llm_config,
            kwargs_llm_config=kwargs_llm_config,
            llm_provider=llm_provider
        )
        
        # Store termination message
        self.terminate_msg = terminate_msg
        
        is_termination_msg = None
        
        # Append termination instructions to system message if a termination message is provided
        if terminate_msg:
            system_message = f"{system_message}\n\nWhen you have completed your response, end your message with \"{terminate_msg}\" to signal that you are done."
            is_termination_msg = lambda x: terminate_msg in (x.get("content", "") or "")
        
        # Initialize base class
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=final_llm_config,
            is_termination_msg=is_termination_msg,
            **kwargs
        )
        
        logger.info(f"Initialized Agent: {name}")
    
    def _prepare_llm_config(
        self,
        name: str,
        config_path: Optional[str],
        llm_config: Optional[Dict[str, Any]],
        kwargs_llm_config: Optional[Dict[str, Any]],
        llm_provider: str
    ) -> tuple[str, Dict[str, Any]]:
        """Prepare the LLM configuration by extracting provider and merging configs.
        
        Args:
            name: Name of the agent (for logging purposes)
            config_path: Optional path to agent configuration file
            llm_config: Optional LLM configuration from parameters
            kwargs_llm_config: Optional LLM configuration from kwargs
            llm_provider: Default LLM provider to use
            
        Returns:
            Tuple of (final_provider, final_llm_config)
        """
        # Extract provider from llm_config if present
        # This allows the provider to be specified in the llm_config directly
        extracted_provider = None
        if llm_config and "provider" in llm_config:
            extracted_provider = llm_config.pop("provider")
            logger.debug(f"Extracted provider '{extracted_provider}' from llm_config for {name}")
            
        # Use provider in this priority order:
        # 1. Extracted from llm_config
        # 2. Explicitly provided llm_provider parameter
        # 3. Default "llm"
        final_provider = extracted_provider or llm_provider
        
        # Determine the final llm_config to use
        # Always start with the base config from config file
        config = load_config(config_path)
        base_llm_config = get_llm_config(config, provider=final_provider)
        
        # Merge configs in this order (later ones take precedence):
        # 1. Base config from config file with correct provider
        # 2. llm_config parameter if provided
        # 3. llm_config from kwargs if provided
        final_llm_config = base_llm_config
        
        if llm_config:
            final_llm_config = {**final_llm_config, **llm_config}
            logger.debug(f"Merged provided llm_config parameter with base config for {name}")
            
        if kwargs_llm_config:
            final_llm_config = {**final_llm_config, **kwargs_llm_config}
            logger.debug(f"Merged kwargs llm_config with previous config for {name}")
        
        logger.debug(f"Final llm_config for {name} using provider {final_provider}: {final_llm_config}")
        
        return final_provider, final_llm_config
    
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
        # Ensure description is a string, not a boolean
        if description is None:
            description = f"Function {function.__name__} provided by {self.name}"
        elif not isinstance(description, str):
            description = str(description)
            
        register_function(
            function,
            caller=self,
            executor=executor_agent,
            description=description
        )
        logger.info(f"Registered function {function.__name__} with caller {self.name} and executor {executor_agent.name}")