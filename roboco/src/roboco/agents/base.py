"""Base agent classes for RoboCo."""

from typing import Dict, List, Optional, Any
import autogen
from loguru import logger

from roboco.core.types import AgentRole, AgentConfig

class RoboCoAgent:
    """Base class for all RoboCo agents."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with its configuration."""
        self.config = config
        self.agent = self._create_agent()
        self._last_message = None
        
    def _create_agent(self):
        """Create the underlying AutoGen agent."""
        if self.config.role == AgentRole.HUMAN:
            return autogen.UserProxyAgent(
                name=self.config.name,
                system_message=self.config.system_message,
                human_input_mode=self.config.human_input_mode,
                code_execution_config={"work_dir": "workspace"},
                llm_config=self.config.llm_config,
                is_termination_msg=self.config.is_termination_msg
            )
        else:
            return autogen.AssistantAgent(
                name=self.config.name,
                system_message=self.config.system_message,
                llm_config=self.config.llm_config,
                human_input_mode=self.config.human_input_mode,
                is_termination_msg=self.config.is_termination_msg
            )
    
    async def process_message(self, message: str, sender: 'RoboCoAgent') -> str:
        """Process a message from another agent."""
        try:
            logger.info(f"Processing message from {sender.config.name}")
            self._last_message = message
            response = await self.agent.generate_response(
                message,
                sender.agent if sender else None
            )
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise
    
    def get_last_message(self) -> Optional[str]:
        """Get the last message processed by this agent."""
        return self._last_message 