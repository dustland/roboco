"""
Agent Factory Module

This module provides a factory for creating agents based on role definitions,
allowing for role-driven agent creation.
"""

import os
from typing import Dict, Any, Optional, Type, List, Union, ClassVar
from loguru import logger
from pathlib import Path

from roboco.core.agent import Agent
from roboco.agents.human_proxy import HumanProxy
from roboco.core.models.config import RobocoConfig
from roboco.core.tool import Tool
from roboco.core.models import AgentConfig, RoleConfig
from roboco.core.config import (
    load_config, 
    get_llm_config, 
    load_roles_config, 
    get_role_config,
    get_validated_role_config,
    create_agent_config
)

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
        # Skip full initialization if already initialized (singleton pattern)
        if AgentFactory._instance is not None:
            # Make sure instance variables are always available
            if not hasattr(self, 'roles_config'):
                self.roles_config = load_roles_config(roles_config_path)
            if not hasattr(self, 'main_config'):
                self.main_config = load_config()
            if not hasattr(self, 'prompts_dir'):
                self.prompts_dir = prompts_dir
            if not hasattr(self, 'agent_registry'):
                self.agent_registry = {}
            return
            
        self.roles_config: Dict = load_roles_config(roles_config_path)
        self.main_config: RobocoConfig = load_config()  # Use core.config to load the main configuration
        self.prompts_dir: str = prompts_dir
        self.agent_registry: Dict[str, Type[Agent]] = {}  # Registry of specialized agent classes
        
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
        
        First attempts to load a detailed markdown prompt from the prompts directory.
        Falls back to a default prompt if no markdown file exists.
        
        Args:
            role_key: The key of the role in the configuration
            
        Returns:
            The system prompt string for the specified role
        """
        # First try to load detailed markdown prompt
        markdown_prompt = self._load_markdown_prompt(role_key)
        if markdown_prompt:
            logger.info(f"Using detailed markdown prompt for role '{role_key}'")
            return markdown_prompt
        
        # If no markdown prompt exists, create a default prompt based on role name
        role_config = get_role_config(self.roles_config, role_key)
        if role_config:
            role_name = role_config.name
            default_prompt = f"You are the {role_name} agent."
            logger.info(f"Using default prompt for role '{role_key}': '{default_prompt}'")
            return default_prompt
        else:
            # Create a generic prompt based on role key
            default_prompt = f"You are the {role_key.replace('_', ' ').title()} agent."
            logger.warning(f"Role '{role_key}' not found in config, using default prompt: '{default_prompt}'")
            return default_prompt
    
    def _get_llm_config(self, role_key: str) -> Optional[Dict[str, Any]]:
        """Get the LLM configuration for a specific role.
        
        Extracts the LLM configuration from the role definition in roles.yaml,
        then uses core.config functions to properly merge with model settings.
        
        Args:
            role_key: The key of the role in the configuration
            
        Returns:
            Dictionary containing LLM configuration or None if not specified
        """
        # Get role-specific config
        role_config = get_role_config(self.roles_config, role_key)
        
        if role_config and role_config.llm:
            # Get role-specific model
            role_model = role_config.llm.get("model")
            
            if role_model:
                # Get model-specific configuration from config.yaml
                model_config = get_llm_config(self.main_config, model=role_model)
                
                # Apply role-specific overrides
                role_llm_config = role_config.llm.copy()
                role_llm_config.pop("model", None)  # Remove model key
                
                # Merge model config with role-specific overrides
                merged_config = {**model_config, **role_llm_config}
                
                logger.info(f"Created merged LLM configuration for role '{role_key}' using model '{role_model}'")
                return merged_config
        
        # If no role-specific model, return the default config
        return get_llm_config(self.main_config)
    
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
        llm_config: Optional[Dict[str, Any]] = None,
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
            llm_config: Optional explicit LLM configuration to use (will be merged with base config)
            **kwargs: Additional arguments passed to the agent constructor
            
        Returns:
            An initialized agent instance (either Agent or HumanProxy)
        """
        # Get the validated role configuration
        role_config = get_role_config(self.roles_config, role_key)
        
        # Get the agent name (from parameter, role config, or role key)
        if name is None:
            if role_config:
                name = role_config.name
            else:
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
        
        # Extract llm_config from kwargs if provided there
        if 'llm_config' in kwargs and llm_config is None:
            llm_config = kwargs.pop('llm_config')
        
        # Determine if this is a human proxy or agent role
        role_type = "agent"  # Default to agent
        if role_config:
            role_type = role_config.type.lower()
        
        # Create validated agent configuration
        agent_config = create_agent_config(
            role_key=role_key,
            name=name,
            system_message=system_message,
            llm_config=llm_config,
            **kwargs
        )
        
        # Set up common parameters for agent creation
        agent_params = {
            "name": agent_config.name,
            "system_message": agent_config.system_message or system_message,
            **kwargs  # Include all additional parameters
        }
        
        # Handle LLM configuration - just get the role config and pass it through
        # Any provider extraction will be handled by Agent.__init__
        if llm_config is None:
            role_llm_config = self._get_llm_config(role_key)
            if role_llm_config:
                agent_params["llm_config"] = role_llm_config
        else:
            # If explicit config provided, use it directly
            agent_params["llm_config"] = llm_config
        
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
        # Ensure we're using the correct registry (from singleton if needed)
        registry = getattr(self, 'agent_registry', None) or getattr(AgentFactory._instance, 'agent_registry', {})
        
        logger.info(f"Agent Registry contains {len(registry)} entries:")
        for role_key, agent_class in registry.items():
            logger.info(f"  - {role_key}: {agent_class.__name__}") 