"""
Base Agent Module

This module defines the Agent class that extends AG2's ConversableAgent.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
from loguru import logger
import traceback

# ag2 and autogen are identical packages
from autogen import ConversableAgent, register_function

from roboco.core.config import load_config, get_llm_config

# Get a logger instance for this module
logger = logger.bind(module=__name__)


class Agent(ConversableAgent):
    """Base agent class that all roboco agents inherit from.
    
    This class extends AG2's ConversableAgent to provide additional functionality:
    1. Integration with roboco's configuration system
    2. Standardized termination message handling
    3. Tool management
    
    The termination message feature allows agents to signal when they have completed
    their response, following AG2's conversation termination pattern. When an agent
    includes the termination message in its response, other agents can recognize it
    and end the conversation.
    
    The termination message roles:
    1. Setter role: An agent that sends termination messages (by setting terminate_msg)
    2. Checker role: An agent that checks for termination messages (by setting check_terminate_msg)
    
    Note: According to AG2's pattern, an agent should take either the setter role OR 
    the checker role, but not both at the same time.
    """

    def __init__(
        self,
        name: str,
        system_message: str,
        config_path: Optional[str] = None,
        terminate_msg: Optional[str] = None,
        check_terminate_msg: Optional[str] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        llm_model: Optional[str] = None,
        human_input_mode: str = "NEVER",
        code_execution_config: Union[Dict[str, Any], bool] = False,
        **kwargs
    ):
        """Initialize an agent.
        
        Args:
            name: Name of the agent
            system_message: System message defining agent behavior
            config_path: Optional path to agent configuration file
            terminate_msg: Optional message to include at the end of responses to signal completion.
                           If provided, this agent takes the "setter" role for termination messages.
            check_terminate_msg: Optional message to check for in received messages.
                                 If provided, this agent takes the "checker" role for termination messages.
                                 Note: According to AG2 pattern, an agent should take either the setter role
                                 OR the checker role, but not both.
            llm_config: Optional LLM configuration. If None, loads from config_path.
            llm_model: The LLM model to use (e.g., "gpt_4o", "deepseek_v3", "claude_3_7_sonnet").
                       This allows different agents to use different LLM models.
            human_input_mode: When to ask for human input. Default: "NEVER"
            code_execution_config: Configuration for code execution
            **kwargs: Additional arguments passed to ConversableAgent
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
        self.check_terminate_msg = check_terminate_msg
        
        # Add current date/time to system message
        system_message = f"{system_message}\n\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Append termination instructions to system message if a termination message is provided
        if terminate_msg:
            system_message = f"{system_message}\n\nWhen you have completed your response, end your message with \"{terminate_msg}\" to signal that you are done."
        
        # Add anti-loop protection instructions with stronger language
        system_message = f"{system_message}\n\nCRITICAL INSTRUCTION: Do not transfer control back to an agent that just transferred to you without doing meaningful work first. This creates an infinite loop. Empty or single-word responses with just 'None' are not permitted. You MUST provide substantive content when responding to handoffs."
        
        # Note: Detailed agent guidelines including file path rules are included via
        # the agent.md file, which is appended to all agent prompts through the
        # AgentFactory._load_markdown_prompt mechanism.
        
        # Create termination message checker function if check_terminate_msg is provided
        is_termination_msg = None
        if check_terminate_msg:
            is_termination_msg = lambda x: check_terminate_msg in (x.get("content", "") or "")
        
        # Initialize base class
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=final_llm_config,
            is_termination_msg=is_termination_msg,
            human_input_mode=human_input_mode,
            code_execution_config=code_execution_config,
            **kwargs
        )
        
        # Initialize handoff tracking
        self.last_handoff_from = None
        self.handoff_count = {}
        
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
            # Check if function has a __name__ attribute (regular functions do, but Tool objects don't)
            if hasattr(function, '__name__'):
                description = f"Function {function.__name__} provided by {self.name}"
            else:
                # For Tool objects, use their name attribute if available, otherwise use a generic description
                if hasattr(function, 'name'):
                    description = f"Tool {function.name} provided by {self.name}"
                else:
                    description = f"Tool provided by {self.name}"
        elif not isinstance(description, str):
            description = str(description)
        
        register_function(
            function,
            caller=self,
            executor=executor_agent,
            description=description
        )
        logger.debug(f"Registered {'tool' if hasattr(function, 'name') else 'function'} with caller {self.name} and executor {executor_agent.name}")
    
    def generate_reply(self, messages: List[Dict[str, Any]]=None, sender=None):
        """Generate a reply to the messages.
        
        This method is called by the AutoGen framework.
        """
        # Track handoffs and detect potential loops
        if sender is not None:
            sender_name = getattr(sender, "name", str(sender))
            
            # Track who we received a message from
            self.last_handoff_from = sender_name
            
            # Increase handoff count for this sender
            if sender_name not in self.handoff_count:
                self.handoff_count[sender_name] = 1
            else:
                self.handoff_count[sender_name] += 1
                
            # Check if this is a potential loop (many handoffs from same sender)
            if self.handoff_count[sender_name] > 3:
                logger.warning(f"⚠️ Potential handoff loop detected: {sender_name} → {self.name} occurred {self.handoff_count[sender_name]} times")
                
                # Log the previous messages to help with debugging
                if messages and len(messages) >= 3:
                    logger.warning("Recent message history:")
                    for i, msg in enumerate(messages[-3:]):
                        content = msg.get("content", "")
                        name = msg.get("name", "unknown")
                        logger.warning(f"  [{i}] {name}: {content[:50]}{'...' if len(content) > 50 else ''}")
                
                # Add a warning message to help break the loop
                if messages and len(messages) > 0:
                    # Check if the last message is from the sender
                    if messages[-1].get("name", "") == sender_name:
                        # Add a hint to break the loop with stronger language
                        messages.append({
                            "role": "system", 
                            "content": f"CRITICAL INSTRUCTION: You've received multiple consecutive handoffs from {sender_name}. This indicates an infinite conversation loop. DO NOT hand control back to {sender_name} immediately. You MUST perform a substantive task or provide meaningful information before any handoff. Empty responses with just 'None' are not permitted and will be rejected."
                        })
        
        try:
            # Call the original method to generate a response
            response = super().generate_reply(messages, sender)
            
            # Check if the response is empty or just "None"
            is_empty_response = False
            if response and isinstance(response, dict) and "content" in response:
                content = response.get("content", "")
                if not content or content == "None" or len(content.strip()) <= 5:
                    is_empty_response = True
                    logger.warning(f"⚠️ Empty response detected from {self.name}: '{content}'")
                    logger.warning(f"This may contribute to handoff loops. Responses should be substantive.")
                    
                    # Log additional information to help debug
                    logger.debug(f"Agent model: {getattr(self, 'llm_config', {}).get('model', 'unknown')}")
                    logger.debug(f"Last handoff from: {self.last_handoff_from}")
                    logger.debug(f"Handoff counts: {self.handoff_count}")
                    
                    # Consider modifying the response to break the loop
                    # We're not automatically changing it per your request, but adding robust logging
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating reply in {self.name}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Create a suitable default response when the API fails
            error_response = {
                "role": "assistant",
                "content": f"ERROR: API call failed - {type(e).__name__}: {str(e)}. Please check logs for details."
            }
            return error_response
    
    def log_api_error(self, exception, messages=None):
        """Log API errors with helpful context."""
        logger.error(f"API Error in {self.name}: {str(exception)}")
        if messages:
            logger.debug(f"Last message: {messages[-1] if messages else 'No messages'}")
        logger.debug(traceback.format_exc())
        
    def add_to_context(self, key: str, value: Any) -> None:
        """
        Add or update an item in the shared context.
        
        Args:
            key: The key to add or update
            value: The value to store
        """
        self.shared_context[key] = value
        
    def update_task_status(self, status: str) -> None:
        """
        Update the status of the current task.
        
        Args:
            status: The new status of the task
        """
        self.shared_context["task_status"] = status
        
    def add_pending_action(self, action: str) -> None:
        """
        Add a pending action to the shared context.
        
        Args:
            action: Description of the action to be performed
        """
        if action not in self.shared_context["pending_actions"]:
            self.shared_context["pending_actions"].append(action)
        
    def mark_action_complete(self, action: str) -> None:
        """
        Mark an action as complete in the shared context.
        
        Args:
            action: Description of the action that was completed
        """
        if action in self.shared_context["pending_actions"]:
            self.shared_context["pending_actions"].remove(action)
        
        if action not in self.shared_context["completed_actions"]:
            self.shared_context["completed_actions"].append(action)
            
    def add_artifact(self, name: str, description: str, value: Any = None) -> None:
        """
        Add an artifact to the shared context.
        
        Args:
            name: Name of the artifact
            description: Description of the artifact
            value: Optional value of the artifact
        """
        self.shared_context["artifacts"][name] = {
            "description": description,
            "created_by": self.name,
            "created_at": datetime.now().isoformat(),
            "value": value
        }
