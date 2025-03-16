"""Human proxy agent implementation."""

from typing import Dict, Any, List, Optional
from autogen import UserProxyAgent
from roboco.core.config import load_config

class HumanProxy(UserProxyAgent):
    """Agent that acts as a proxy for human users, enabling natural interaction with other agents.
    
    This agent extends AG2's UserProxyAgent to provide additional functionality:
    1. Configurable termination message handling
    2. Automatic propagation of termination messages to other agents
    3. Integration with roboco's configuration system
    
    The termination message is used to signal the end of a conversation, following
    AG2's conversation termination pattern. When an agent includes the termination
    message in its response, this agent will recognize it and end the conversation.
    """

    def __init__(
        self,
        name: str = "Human",
        system_message: Optional[str] = None,
        config_path: Optional[str] = None,
        human_input_mode: str = "NEVER",
        terminate_msg: Optional[str] = None,
        **kwargs
    ):
        """Initialize the HumanProxy agent.
        
        Args:
            name: Name of the agent
            system_message: Custom system message for the agent
            config_path: Optional path to agent configuration file
            human_input_mode: When to request human input
            terminate_msg: Message to send to end the conversation. If None, uses the value from config.
            **kwargs: Additional arguments passed to UserProxyAgent
        """
        if system_message is None:
            system_message = """You are a proxy for a human user, enabling natural interaction with other agents.
            Your role is to:
            1. Express user needs and requirements clearly
            2. Ask relevant follow-up questions
            3. Request clarification when needed
            4. Keep conversations focused and productive
            5. Provide feedback and guidance to other agents"""

        # Load configuration
        config = load_config(config_path)
        
        # Use termination message from config if none is provided
        if terminate_msg is None:
            terminate_msg = config.terminate_msg
            
        self.terminate_msg = terminate_msg
        
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=human_input_mode,
            code_execution_config={"use_docker": False},  # Disable Docker for code execution
            is_termination_msg=lambda x: terminate_msg in (x.get("content", "") or ""),
            **kwargs
        ) 