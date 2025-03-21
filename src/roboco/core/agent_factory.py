"""
Agent Factory Module

This module provides a factory for creating agents based on role definitions,
allowing for role-driven agent creation.
"""

import os
import yaml
from typing import Dict, Any, Optional, Type, List, Union, ClassVar
from loguru import logger

from roboco.core.agent import Agent, HumanProxy
from roboco.core.tool import Tool

class AgentFactory:
    """Factory for creating agents based on role definitions.
    
    This class follows the singleton pattern to ensure there is only
    one central registry of agent classes across the application.
    """
    
    # Singleton instance
    _instance: ClassVar[Optional['AgentFactory']] = None
    
    @classmethod
    def get_instance(cls, **kwargs) -> 'AgentFactory':
        """Get the singleton instance of AgentFactory.
        
        Args:
            **kwargs: Initialization parameters (only used when creating a new instance)
            
        Returns:
            The singleton AgentFactory instance
        """
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    def __init__(
        self,
        roles_config_path: str = "config/roles.yaml",
        prompts_dir: str = "config/prompts",
    ):
        """Initialize the agent factory.
        
        Args:
            roles_config_path: Path to the roles configuration file
            prompts_dir: Directory containing markdown files with detailed role prompts
        """
        # Skip initialization if already initialized (singleton pattern)
        if AgentFactory._instance is not None:
            return
            
        self.roles_config = self._load_roles_config(roles_config_path)
        self.prompts_dir = prompts_dir
        self.agent_registry = {}  # Registry of specialized agent classes
        
    def _load_roles_config(self, config_path: str) -> Dict[str, Any]:
        """Load the roles configuration from YAML file.
        
        Args:
            config_path: Path to the roles configuration file
            
        Returns:
            Dictionary containing role configurations
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"Successfully loaded roles configuration from {config_path}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load roles config from {config_path}: {str(e)}")
            logger.warning("Using default empty configuration")
            return {"roles": {}}
    
    def _load_markdown_prompt(self, role_key: str) -> Optional[str]:
        """Load a detailed prompt from a markdown file.
        
        Args:
            role_key: The key of the role to load the prompt for
            
        Returns:
            The contents of the markdown file, or None if the file doesn't exist
        """
        file_path = os.path.join(self.prompts_dir, f"{role_key}.md")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                prompt = file.read()
                logger.info(f"Loaded detailed prompt from {file_path}")
                return prompt
        except Exception as e:
            logger.warning(f"Failed to load markdown prompt from {file_path}: {str(e)}")
            return None
    
    def _get_system_prompt(self, role_key: str) -> str:
        """Get the system prompt for a specific role.
        
        First attempts to load a detailed markdown prompt.
        Falls back to the compact prompt from roles.yaml if no markdown file exists.
        Finally falls back to a default prompt if neither exists.
        
        Args:
            role_key: The key of the role in the configuration
            
        Returns:
            The system prompt string for the specified role
        """
        # First try to load detailed markdown prompt
        markdown_prompt = self._load_markdown_prompt(role_key)
        if markdown_prompt:
            return markdown_prompt
        
        # Fall back to compact prompt from roles.yaml
        try:
            return self.roles_config["roles"][role_key]["system_prompt"]
        except (KeyError, TypeError):
            logger.warning(f"System prompt for '{role_key}' not found in config, using default")
            return f"You are the {role_key.replace('_', ' ').title()} agent."
    
    def register_agent_class(self, role_key: str, agent_class: Type[Agent]):
        """Register a specialized agent class for a specific role.
        
        Args:
            role_key: The key of the role in the configuration
            agent_class: The specialized agent class to use for this role
        """
        self.agent_registry[role_key] = agent_class
        logger.info(f"Registered specialized agent class {agent_class.__name__} for role '{role_key}'")
    
    def create_agent(
        self,
        role_key: str,
        name: Optional[str] = None,
        system_message: Optional[str] = None,
        tools: Optional[List[Union[Tool, Dict]]] = None,
        **kwargs
    ) -> Agent:
        """Create an agent for a specific role.
        
        If a specialized agent class is registered for the role, that class is used.
        Otherwise, a basic Agent or HumanProxy instance is created based on the role configuration.
        
        Args:
            role_key: The key of the role in the configuration
            name: Optional custom name for the agent (defaults to role name from config)
            system_message: Optional custom system message (overrides role prompt)
            tools: Optional list of tools to register with the agent
            **kwargs: Additional arguments passed to the agent constructor
            
        Returns:
            An initialized agent instance (either Agent or HumanProxy)
        """
        # Get the agent name (from parameter, config, or role key)
        if name is None:
            try:
                name = self.roles_config["roles"][role_key]["name"]
            except (KeyError, TypeError):
                name = role_key.replace('_', ' ').title()
        
        # Ensure the name doesn't contain whitespace (AG2 requirement)
        name = name.replace(' ', '_')
        
        # Get the system message if not provided
        if system_message is None:
            system_message = self._get_system_prompt(role_key)
        
        # Extract tools from kwargs to handle them separately
        if 'tools' in kwargs:
            if tools is None:
                tools = kwargs.pop('tools')
            else:
                tools.extend(kwargs.pop('tools'))
        
        # Determine if this is a human proxy or agent role
        role_type = "agent"  # Default to agent
        try:
            role_type = self.roles_config["roles"][role_key].get("type", "agent").lower()
        except (KeyError, TypeError):
            pass
        
        # Set up common parameters for agent creation
        agent_params = {
            "name": name,
            "system_message": system_message,
            **kwargs  # Include all additional parameters
        }
        
        # Create agent based on role type and registry
        if role_key in self.agent_registry:
            # Create specialized agent using the registered class
            agent_class = self.agent_registry[role_key]
            logger.info(f"Creating {agent_class.__name__} for role '{role_key}'")
            return agent_class(**agent_params)
        elif role_type == "human_proxy":
            # Create a HumanProxy
            logger.info(f"Creating HumanProxy for role '{role_key}'")
            # Set code_execution_config with use_docker=False
            if "code_execution_config" not in agent_params:
                agent_params["code_execution_config"] = {"work_dir": "workspace", "use_docker": False}
            elif agent_params["code_execution_config"] is not None:
                agent_params["code_execution_config"]["use_docker"] = False
            return HumanProxy(**agent_params)
        else:
            # Create a basic Agent
            logger.info(f"Creating Agent for role '{role_key}'")
            return Agent(**agent_params)
        
    def debug_registry(self):
        """Print the current state of the agent registry for debugging purposes."""
        logger.info(f"Agent Registry contains {len(self.agent_registry)} entries:")
        for role_key, agent_class in self.agent_registry.items():
            logger.info(f"  - {role_key}: {agent_class.__name__}") 