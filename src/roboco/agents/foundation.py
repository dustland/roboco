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

class ToolExecutorAgent(ConversableAgent):
    """
    An agent specifically designed to execute tools (functions) on behalf of other agents.
    It typically does not use an LLM to generate replies but executes registered functions.
    It directly extends autogen's ConversableAgent.
    """
    def __init__(
        self,
        name: str,
        system_message: Optional[str] = "Tool execution agent.", # Minimal system message
        human_input_mode: str = "NEVER",
        code_execution_config: Optional[Dict[str, Any] | bool] = False, # No arbitrary code execution
        default_auto_reply: Optional[str] = "", # Reply with empty string after execution by default
        llm_config: Optional[LLMConfig | Dict[str, Any] | bool] = False, # No LLM needed by default
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
