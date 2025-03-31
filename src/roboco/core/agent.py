"""
Base Agent Module

This module defines the Agent class that extends AG2's AssistantAgent.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
from loguru import logger
import traceback
import json

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
        llm_model: Optional[str] = None,
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
            llm_model: The LLM model to use (e.g., "gpt_4o", "deepseek_v3", "claude_3_7_sonnet").
                       This allows different agents to use different LLM models.
            **kwargs: Additional arguments passed to AssistantAgent
        """
        # Extract llm_config from kwargs if provided
        kwargs_llm_config = kwargs.pop('llm_config', None)
        
        # Prepare the LLM configuration using the internal method
        final_model, final_llm_config = self._prepare_llm_config(
            name=name,
            config_path=config_path,
            llm_config=llm_config,
            kwargs_llm_config=kwargs_llm_config,
            llm_model=llm_model
        )
        
        # Store termination message
        self.terminate_msg = terminate_msg
        
        is_termination_msg = None
        
        system_message = f"{system_message}\n\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Add handoff reason requirement to all agents
        system_message = f"{system_message}\n\nWhen handing off to another agent, you MUST include 'HANDOFF REASON:' followed by a clear explanation of why you are handing off."
        
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
        
        logger.info(f"Initialized Agent: {name} with model: {final_llm_config.get('model', 'unknown')}")
    
    def _prepare_llm_config(
        self,
        name: str,
        config_path: Optional[str],
        llm_config: Optional[Dict[str, Any]],
        kwargs_llm_config: Optional[Dict[str, Any]],
        llm_model: Optional[str] = "claude-3-5-sonnet-20241022"
    ) -> tuple[str, Dict[str, Any]]:
        """Prepare the LLM configuration by extracting model and merging configs.
        
        Args:
            name: Name of the agent (for logging purposes)
            config_path: Optional path to agent configuration file
            llm_config: Optional LLM configuration from parameters
            kwargs_llm_config: Optional LLM configuration from kwargs
            llm_model: Optional model key to use (e.g., "gpt_4o", "deepseek_v3")
            
        Returns:
            Tuple of (final_model, final_llm_config)
        """
        # Extract model from llm_config if present
        # This allows the model to be specified in the llm_config directly
        extracted_model = None
        if llm_config and "model" in llm_config:
            extracted_model = llm_config.pop("model")
            logger.debug(f"Extracted model '{extracted_model}' from llm_config for {name}")
            
        # Use model in this priority order:
        # 1. Extracted from llm_config
        # 2. Explicitly provided llm_model parameter
        # 3. Default (None will use default_model in get_llm_config)
        final_model = extracted_model or llm_model
        
        # Determine the final llm_config to use
        # Start with the model-specific configuration from config file
        config = load_config(config_path)
        base_llm_config = get_llm_config(config, model=final_model)
        
        # Merge configs in this order (later ones take precedence):
        # 1. Base config from config file with correct model
        # 2. llm_config parameter if provided
        # 3. llm_config from kwargs if provided
        final_llm_config = base_llm_config
        
        if llm_config:
            final_llm_config = {**final_llm_config, **llm_config}
            logger.debug(f"Merged provided llm_config parameter with base config for {name}")
            
        if kwargs_llm_config:
            final_llm_config = {**final_llm_config, **kwargs_llm_config}
            logger.debug(f"Merged kwargs llm_config with previous config for {name}")
        
        logger.debug(f"Final llm_config for {name} using model {final_model}: {final_llm_config}")
        
        return final_model, final_llm_config
    
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
        # logger.info(f"Registered function {function.__name__} with caller {self.name} and executor {executor_agent.name}")
        
    def generate_reply(self, messages: List[Dict[str, Any]]=None, sender=None):
        """Generate a reply to the messages.
        
        This method is called by the AutoGen framework.
        """
        try:
            # Call the original method
            return super().generate_reply(messages, sender)
        except Exception as e:
            self.log_api_error(e, messages)
            
            # Create a suitable default response when the API fails
            error_response = {
                "role": "assistant",
                "content": f"ERROR: API call failed - {type(e).__name__}: {str(e)}. Please check logs for details."
            }
            return error_response
    
    def log_api_error(self, error: Exception, messages: List[Dict[str, Any]]) -> None:
        """Log detailed information about API errors.
        
        Args:
            error: The exception that occurred
            messages: The messages that were being processed
        """
        # Prepare debug information
        error_type = type(error).__name__
        error_message = str(error)
        tb = traceback.format_exc()
        
        # Extract model information
        model_info = {}
        if hasattr(self, "llm_config"):
            model_info = {
                "model": self.llm_config.get("model", "unknown"),
                "api_type": self.llm_config.get("api_type", "unknown"),
                "base_url": self.llm_config.get("base_url", "unknown")
            }
        
        # Get message summary
        message_summary = []
        for msg in messages[-5:]:  # Get the last 5 messages for context
            role = msg.get("role", "unknown")
            content_preview = str(msg.get("content", ""))[:100] + "..." if len(str(msg.get("content", ""))) > 100 else str(msg.get("content", ""))
            tool_calls = None
            if "tool_calls" in msg:
                tool_calls = []
                for tool_call in msg.get("tool_calls", []):
                    if "id" in tool_call:
                        tool_id = tool_call["id"]
                        tool_id_length = len(tool_id)
                        tool_calls.append({"id": tool_id, "id_length": tool_id_length})
            
            message_summary.append({"role": role, "content_preview": content_preview, "tool_calls": tool_calls})
        
        # Log the error
        logger.error(f"API Error in agent {self.name}")
        logger.error(f"Error: {error_type} - {error_message}")
        logger.error(f"Model info: {json.dumps(model_info, indent=2)}")
        logger.error(f"Message summary: {json.dumps(message_summary, indent=2)}")
        logger.error(f"Traceback: {tb}")
        
        # Check for specific error types and add targeted advice
        if "tool_call" in error_message and "id" in error_message:
            logger.error("TOOL ID ERROR DETECTED: This may be caused by a tool call ID that exceeds the maximum length allowed by the API.")
            logger.error("For Claude models, tool call IDs must be 40 characters or less.")
