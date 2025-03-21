"""
Agent Factory Module

This module provides a factory for creating agents based on role definitions,
allowing for both prompt-driven agents and specialized agent classes.
"""

import os
import yaml
from typing import Dict, Any, Optional, Type, List, Union
from loguru import logger

from roboco.core.agent import Agent
from roboco.core.tool import Tool

# Import specialized agent classes
try:
    from roboco.agents.human import HumanProxy
    from roboco.agents import (
        Executive,
        ProductManager,
        SoftwareEngineer,
        ReportWriter,
        RoboticsScientist
    )
    specialized_agents_available = True
except ImportError:
    logger.warning("Some specialized agent classes could not be imported")
    specialized_agents_available = False

class AgentFactory:
    """Factory for creating agents based on role definitions."""
    
    def __init__(
        self,
        roles_config_path: str = "config/roles.yaml",
        prompts_dir: str = "config/prompts",
        register_specialized_agents: bool = True,
    ):
        """Initialize the agent factory.
        
        Args:
            roles_config_path: Path to the roles configuration file
            prompts_dir: Directory containing markdown files with detailed role prompts
            register_specialized_agents: Whether to automatically register specialized agent classes
        """
        self.roles_config = self._load_roles_config(roles_config_path)
        self.prompts_dir = prompts_dir
        self.agent_registry = {}  # Registry of specialized agent classes
        
        # Register specialized agent classes if requested
        if register_specialized_agents:
            self._register_specialized_agents()
        
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
    
    def _register_specialized_agents(self):
        """Register all available specialized agent classes."""
        # Register HumanProxy - always needed for tool execution
        if 'HumanProxy' in globals():
            self.register_agent_class("human_proxy", HumanProxy)
        
        # Only register other specialized agents if they're available
        if specialized_agents_available:
            # Register core specialized agent classes
            try:
                self.register_agent_class("executive", Executive)
                self.register_agent_class("product_manager", ProductManager)
                self.register_agent_class("software_engineer", SoftwareEngineer)
                self.register_agent_class("report_writer", ReportWriter)
                self.register_agent_class("robotics_scientist", RoboticsScientist)
            except Exception as e:
                logger.warning(f"Error registering specialized agents: {str(e)}")
        
        logger.info(f"Completed registration of specialized agent classes")
    
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
        Otherwise, a basic Agent instance is created with the role's system prompt.
        
        Args:
            role_key: The key of the role in the configuration
            name: Optional custom name for the agent (defaults to role name from config)
            system_message: Optional custom system message (overrides role prompt)
            tools: Optional list of tools to register with the agent
            **kwargs: Additional arguments passed to the agent constructor
            
        Returns:
            An initialized agent instance
        """
        # Get the agent name (from parameter, config, or role key)
        if name is None:
            try:
                name = self.roles_config["roles"][role_key]["name"]
            except (KeyError, TypeError):
                name = role_key.replace('_', ' ').title()
        
        # Get the system message if not provided
        if system_message is None:
            system_message = self._get_system_prompt(role_key)
        
        # Check if we have a specialized agent class for this role
        if role_key in self.agent_registry:
            agent_class = self.agent_registry[role_key]
            logger.info(f"Creating specialized {agent_class.__name__} agent for role '{role_key}'")
            return agent_class(
                name=name,
                system_message=system_message,
                **kwargs
            )
        
        # Otherwise, create a basic agent with the role's system prompt
        logger.info(f"Creating generic agent for role '{role_key}'")
        return Agent(
            name=name,
            system_message=system_message,
            tools=tools,
            **kwargs
        ) 