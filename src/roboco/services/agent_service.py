"""
Agent Service

This module provides services for managing agents, including agent creation,
configuration, and communication.
"""

from typing import Dict, Any, List, Optional, Type
import os
import json
from datetime import datetime
from loguru import logger

from roboco.core.config import load_config, get_llm_config, get_workspace
from roboco.core.agent import Agent
from roboco.agents.human_proxy import HumanProxy


class AgentService:
    """
    Service for managing agents and agent-related operations.
    
    This service follows the DDD principles by encapsulating agent-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self):
        """Initialize the agent service."""
        # Load global configuration
        self.config = load_config()
        
        # Set up workspace directory
        self.workspace_dir = get_workspace()
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Agent registry
        self._agent_types: Dict[str, Type[Agent]] = {}
        self._register_core_agent_types()
    
    def _register_core_agent_types(self):
        """Register the core agent types."""
        self._agent_types = {}
        self._agent_types["Agent"] = Agent
        self._agent_types["HumanProxy"] = HumanProxy
        
        # Dynamically discover and register other agent types
        try:
            from roboco.agents.robotics_scientist import RoboticsScientist
            self._agent_types["RoboticsScientist"] = RoboticsScientist
        except ImportError:
            pass
            
        try:
            from roboco.agents.genesis_agent import GenesisAgent
            self._agent_types["GenesisAgent"] = GenesisAgent
        except ImportError:
            pass
    
    def register_agent_type(self, name: str, agent_class: Type[Agent]):
        """
        Register a new agent type.
        
        Args:
            name: The name of the agent type.
            agent_class: The agent class.
        """
        self._agent_types[name] = agent_class
    
    async def list_agent_types(self) -> List[Dict[str, Any]]:
        """
        List all available agent types.
        
        Returns:
            List of agent type information dictionaries.
        """
        result = []
        
        for name, agent_class in self._agent_types.items():
            # Get agent description from docstring
            description = agent_class.__doc__ or ""
            description = description.strip().split("\n")[0] if description else ""
            
            result.append({
                "name": name,
                "description": description,
                "base_class": agent_class.__base__.__name__
            })
        
        # Sort by name
        result.sort(key=lambda x: x["name"])
        
        return result
    
    async def get_agent_type(self, name: str) -> Dict[str, Any]:
        """
        Get details for a specific agent type.
        
        Args:
            name: The name of the agent type.
            
        Returns:
            Agent type information dictionary.
            
        Raises:
            ValueError: If the agent type is not found.
        """
        if name not in self._agent_types:
            raise ValueError(f"Agent type '{name}' not found")
        
        agent_class = self._agent_types[name]
        
        # Get agent description from docstring
        description = agent_class.__doc__ or ""
        description = description.strip() if description else ""
        
        # Get method information
        methods = []
        for method_name in dir(agent_class):
            if method_name.startswith("_"):
                continue
                
            method = getattr(agent_class, method_name)
            if callable(method):
                method_doc = method.__doc__ or ""
                method_doc = method_doc.strip().split("\n")[0] if method_doc else ""
                
                methods.append({
                    "name": method_name,
                    "description": method_doc
                })
        
        return {
            "name": name,
            "description": description,
            "base_class": agent_class.__base__.__name__,
            "methods": methods
        }
    
    async def create_agent(self, agent_type: str, name: str, 
                          system_prompt: Optional[str] = None,
                          llm_config: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Create a new agent instance.
        
        Args:
            agent_type: The type of agent to create.
            name: The name of the agent instance.
            system_prompt: Optional system prompt to override the default.
            llm_config: Optional LLM configuration to override the default.
            **kwargs: Additional arguments for the agent constructor.
            
        Returns:
            Agent instance information dictionary.
            
        Raises:
            ValueError: If the agent type is not found.
        """
        if agent_type not in self._agent_types:
            raise ValueError(f"Agent type '{agent_type}' not found")
        
        agent_class = self._agent_types[agent_type]
        
        # Create the agent instance
        agent = agent_class(
            name=name,
            system_prompt=system_prompt,
            llm_config=llm_config or get_llm_config(),
            **kwargs
        )
        
        # Return agent information
        return {
            "id": id(agent),  # Use object ID as a unique identifier
            "type": agent_type,
            "name": name,
            "system_prompt": agent.system_prompt
        }
