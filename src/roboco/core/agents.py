from typing import Optional, Dict, Any
from autogen import ConversableAgent, LLMConfig # Removed AssistantAgent, UserProxyAgent

class Agent(ConversableAgent):
    """
    A general-purpose conversational agent capable of utilizing tools and 
    participating in discussions. It directly extends autogen's ConversableAgent.
    """
    def __init__(
        self,
        name: str,
        system_message: Optional[str] = "You are a helpful AI Assistant.",
        llm_config: Optional[LLMConfig | Dict[str, Any] | bool] = None,
        human_input_mode: str = "TERMINATE",
        code_execution_config: Optional[Dict[str, Any] | bool] = False,
        **kwargs,
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            human_input_mode=human_input_mode,
            code_execution_config=code_execution_config,
            **kwargs,
        )
        # Add any Roboco-specific initializations here if needed in the future

class UserAgent(ConversableAgent):
    """
    A user proxy agent that handles both human interaction and tool execution,
    following AG2/AutoGen design patterns. This agent can:
    
    1. Serve as a proxy for human users (with human_input_mode="ALWAYS" or "TERMINATE")
    2. Execute tools and functions on behalf of other agents (with human_input_mode="NEVER")
    3. Handle code execution when configured appropriately
    
    This matches the typical UserProxyAgent pattern in AG2 where a single agent
    handles both user interface concerns and tool execution capabilities.
    """
    def __init__(
        self,
        name: str,
        system_message: Optional[str] = "A human admin.",
        human_input_mode: str = "NEVER",  # Default to tool execution mode
        code_execution_config: Optional[Dict[str, Any] | bool] = False,
        default_auto_reply: Optional[str] = "",
        llm_config: Optional[LLMConfig | Dict[str, Any] | bool] = False,  # No LLM by default
        **kwargs,
    ):
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=human_input_mode,
            code_execution_config=code_execution_config,
            default_auto_reply=default_auto_reply,
            llm_config=llm_config,
            **kwargs,
        )
        # Add any Roboco-specific initializations here
