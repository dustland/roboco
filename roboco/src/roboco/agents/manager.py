"""Manager for coordinating RoboCo agents."""

from typing import Dict, Optional
from loguru import logger

from roboco.core.types import AgentRole
from roboco.agents.roles.human import HumanAgent
from roboco.agents.roles.executive import ExecutiveBoardAgent
from roboco.agents.roles.product import ProductManagerAgent

class AgentManager:
    """Manages all agents in the RoboCo system."""
    
    def __init__(self):
        """Initialize the agent manager."""
        self.agents: Dict[AgentRole, autogen.ConversableAgent] = {}
        self._setup_default_agents()
    
    def _setup_default_agents(self):
        """Set up the default set of agents."""
        self.register_agent(HumanAgent())
        self.register_agent(ExecutiveBoardAgent())
        self.register_agent(ProductManagerAgent())
        logger.info("Default agents initialized")
    
    def register_agent(self, agent) -> None:
        """Register a new agent with the manager."""
        if not hasattr(agent, 'role'):
            logger.error(f"Agent {agent.name} does not have a role attribute")
            return
            
        if agent.role in self.agents:
            logger.warning(f"Replacing existing agent for role {agent.role}")
        self.agents[agent.role] = agent
        logger.info(f"Registered agent {agent.name} for role {agent.role}")
    
    def get_agent(self, role: AgentRole):
        """Get an agent by its role."""
        return self.agents.get(role)
    
    async def send_message(self, 
                          from_role: AgentRole, 
                          to_role: AgentRole, 
                          message: str) -> Optional[str]:
        """Send a message from one agent to another."""
        sender = self.get_agent(from_role)
        receiver = self.get_agent(to_role)
        
        if not sender or not receiver:
            logger.error(f"Invalid sender ({from_role}) or receiver ({to_role})")
            return None
        
        try:
            logger.info(f"Sending message from {from_role} to {to_role}")
            response = await receiver.process_message(message, sender)
            logger.info(f"Received response from {to_role}")
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return None 