"""
Team Builder Module

This module provides a builder pattern for creating teams with different agent compositions
based on role configurations. It simplifies the process of creating and configuring teams.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Type, Set, Union, ClassVar
from loguru import logger

from roboco.core import Team, Agent, AgentFactory, Tool
from roboco.tools.fs import FileSystemTool
from roboco.tools.browser_use import BrowserUseTool

class TeamBuilder:
    """Builder for creating teams with different agent compositions.
    
    This class follows the singleton pattern to ensure there is only one
    central team builder across the application.
    """
    
    # Singleton instance
    _instance: ClassVar[Optional['TeamBuilder']] = None
    
    @classmethod
    def get_instance(cls, **kwargs) -> 'TeamBuilder':
        """Get the singleton instance of TeamBuilder.
        
        Args:
            **kwargs: Initialization parameters (only used when creating a new instance)
            
        Returns:
            The singleton TeamBuilder instance
        """
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance
    
    def __init__(
        self,
        teams_config_path: str = "config/teams.yaml",
        **agent_factory_kwargs
    ):
        """Initialize the team builder.
        
        Args:
            teams_config_path: Path to the teams configuration file (YAML)
            **agent_factory_kwargs: Additional keyword arguments to pass to the AgentFactory
        """
        # Skip initialization if already initialized (singleton pattern)
        if TeamBuilder._instance is not None:
            return
            
        # Get the singleton AgentFactory instance
        self.agent_factory = AgentFactory.get_instance(**agent_factory_kwargs)
        
        # Initialize collections
        self.selected_roles: List[str] = []
        self.tools: Dict[str, List[Tool]] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.handoff_definitions: List[Dict[str, Any]] = []
        self.tool_executor_role: Optional[str] = None
        
        # Initialize team loading configuration
        self.teams_config_path = teams_config_path
        self.teams_config = self._load_teams_config(teams_config_path)
        
        # Initialize available tools
        self.available_tools = {
            "fs": lambda: FileSystemTool(
                name="fs",
                description="Tool for interacting with the file system"
            ),
            "browser_use": lambda: BrowserUseTool(
                name="browser_use",
                description="Tool for browsing the web and interacting with websites"
            )
        }
    
    def _load_teams_config(self, config_path: str) -> Dict[str, Any]:
        """Load the teams configuration from YAML file.
        
        Args:
            config_path: Path to the teams configuration file
            
        Returns:
            Dictionary containing team configurations
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"Successfully loaded teams configuration from {config_path}")
                return config
        except Exception as e:
            logger.warning(f"Failed to load teams config from {config_path}: {str(e)}")
            logger.warning("Using default empty configuration")
            return {"teams": {}}
    
    def get_team_config(self, team_key: str) -> Dict[str, Any]:
        """Get the configuration for a specific team.
        
        Retrieves team configuration from the global teams.yaml file.
        
        Args:
            team_key: The key of the team in the configuration
            
        Returns:
            The team configuration
        """
        # Get the team configuration from the global teams.yaml
        try:
            team_config = self.teams_config["teams"][team_key].copy()
            return team_config
        except (KeyError, TypeError):
            logger.warning(f"Team '{team_key}' not found in config file {self.teams_config_path}")
            raise KeyError(f"Team '{team_key}' not found in configuration")
    
    def with_roles(self, *role_keys: str) -> 'TeamBuilder':
        """Select the roles to include in the team.
        
        Args:
            *role_keys: Keys of the roles to include
            
        Returns:
            The builder instance for method chaining
        """
        self.selected_roles = list(role_keys)
        return self
    
    def with_tool_executor(self, role_key: str = "human_proxy") -> 'TeamBuilder':
        """Set the role that will execute tools for other agents.
        
        Args:
            role_key: Key of the role that will execute tools
            
        Returns:
            The builder instance for method chaining
        """
        self.tool_executor_role = role_key
        # Make sure the tool executor is in the selected roles
        if role_key not in self.selected_roles:
            self.selected_roles.append(role_key)
        return self
    
    def with_tools(self, role_key: str, tools: List[Tool]) -> 'TeamBuilder':
        """Add tools to a specific role.
        
        Args:
            role_key: Key of the role to add tools to
            tools: List of tools to add
            
        Returns:
            The builder instance for method chaining
        """
        self.tools[role_key] = tools
        return self
    
    def with_agent_config(self, role_key: str, **kwargs) -> 'TeamBuilder':
        """Configure specific parameters for an agent.
        
        Args:
            role_key: Key of the role to configure
            **kwargs: Configuration parameters for the agent
            
        Returns:
            The builder instance for method chaining
        """
        self.agent_configs[role_key] = kwargs
        return self
    
    def with_handoff(self, from_role: str, to_role: str, condition: Optional[Dict[str, Any]] = None) -> 'TeamBuilder':
        """Define a handoff between agents.
        
        Args:
            from_role: Role key of the agent handing off
            to_role: Role key of the agent receiving the handoff
            condition: Optional condition for the handoff
            
        Returns:
            The builder instance for method chaining
        """
        self.handoff_definitions.append({
            "from_role": from_role,
            "to_role": to_role,
            "condition": condition
        })
        return self
    
    def with_circular_workflow(self, *role_keys: str) -> 'TeamBuilder':
        """Define a circular workflow between multiple agents.
        
        Args:
            *role_keys: Role keys of the agents in the workflow order
            
        Returns:
            The builder instance for method chaining
        """
        roles = list(role_keys)
        for i, role in enumerate(roles):
            next_role = roles[(i + 1) % len(roles)]
            self.handoff_definitions.append({
                "from_role": role,
                "to_role": next_role,
                "condition": None
            })
        return self
    
    def create_team_from_config(self, team_key: str, **kwargs) -> Team:
        """Create a team based on configuration files.
        
        Args:
            team_key: The key of the team in the configuration
            **kwargs: Additional arguments to override configuration values
            
        Returns:
            An initialized Team instance
        """
        # Get the team configuration
        team_config = self.get_team_config(team_key)
        
        # Override with any kwargs
        team_config.update(kwargs)
        
        # Configure a new builder based on the team config
        builder = TeamBuilder.get_instance()
        
        # Configure roles
        if "roles" in team_config:
            builder.with_roles(*team_config["roles"])
        
        # Configure tool executor
        if "tool_executor" in team_config:
            builder.with_tool_executor(team_config["tool_executor"])
        
        # Configure tools
        if "tools" in team_config:
            tool_executor = team_config.get("tool_executor", "human_proxy")
            tool_instances = []
            
            for tool_name in team_config["tools"]:
                if tool_name in builder.available_tools:
                    tool_instances.append(builder.available_tools[tool_name]())
            
            if tool_instances:
                builder.with_tools(tool_executor, tool_instances)
                
        # Configure agent-specific configurations
        if "agent_configs" in team_config:
            for role, config in team_config["agent_configs"].items():
                builder.with_agent_config(role, **config)
        
        # Configure handoffs if workflow is defined
        if "workflow" in team_config:
            for handoff in team_config["workflow"]:
                from_role = handoff.get("from")
                to_role = handoff.get("to")
                condition = handoff.get("condition")
                
                if from_role and to_role:
                    builder.with_handoff(from_role, to_role, condition)
        
        # Configure output directory
        output_dir = team_config.get("output_dir", "workspace/team_output")
        
        # Build the team
        team_name = team_config.get("name", team_key)
        return builder.build(name=team_name, output_dir=output_dir)
    
    def build(self, team_class: Type[Team] = Team, name: str = None, **team_kwargs) -> Team:
        """Build the team with the configured parameters.
        
        Args:
            team_class: Optional custom Team class to use
            name: Optional name for the team
            **team_kwargs: Additional arguments to pass to the Team constructor
            
        Returns:
            An initialized Team instance with all configured agents
        """
        # Create an empty agents dictionary
        agents = {}
        
        # Create the agent factory
        agent_factory = AgentFactory.get_instance()
        
        # Created a set of processed roles to avoid duplicates
        processed_roles = set()
        
        # Create each agent in the team
        for role in self.selected_roles:
            if role in processed_roles:
                continue
                
            processed_roles.add(role)
            
            # Get the agent configuration if specified
            agent_config = self.agent_configs.get(role, {})
            
            # Create the agent
            agent = agent_factory.create_agent(
                role_key=role,
                **agent_config
            )
            
            # Register tools if present
            if role in self.tools and hasattr(agent, "register_tool"):
                for tool in self.tools[role]:
                    try:
                        agent.register_tool(tool)
                    except Exception as e:
                        logger.error(f"Failed to register tool with {role}: {e}")
            
            # Add the agent to the dictionary
            agents[role] = agent
            
        # Create the team
        logger.info(f"Building team with {len(agents)} agents: {', '.join(agents.keys())}")
        team = team_class(name=name or "Team", agents=agents, **team_kwargs)
        
        # Register handoffs between agents
        self._register_handoffs(team)
                
        # Set the tool executor if configured
        if self.tool_executor_role and self.tool_executor_role in agents:
            # Store the executor in the team's shared context
            team.shared_context["tool_executor"] = agents[self.tool_executor_role]
            logger.info(f"Set {self.tool_executor_role} as tool executor")
            
            # Register tools with the executor
            executor = agents[self.tool_executor_role]
            for role, agent in agents.items():
                if role != self.tool_executor_role and hasattr(agent, "register_tools_with_executor"):
                    try:
                        agent.register_tools_with_executor(executor)
                        logger.info(f"Registered tools from {role} with executor {self.tool_executor_role}")
                    except Exception as e:
                        logger.error(f"Failed to register tools from {role} with executor: {e}")
                
        return team
    
    def _register_handoffs(self, team: Team) -> None:
        """Register handoffs between agents in the team.
        
        Args:
            team: The team object to register handoffs for
        """
        if not self.handoff_definitions:
            return
            
        from autogen import register_hand_off, AfterWork
        
        for handoff in self.handoff_definitions:
            from_role = handoff["from_role"]
            to_role = handoff["to_role"]
            
            if from_role in team.agents and to_role in team.agents:
                from_agent = team.get_agent(from_role)
                to_agent = team.get_agent(to_role)
                
                # Register the handoff
                register_hand_off(
                    agent=from_agent,
                    hand_to=AfterWork(agent=to_agent)
                )
                logger.info(f"Registered handoff from {from_role} to {to_role}")
            else:
                logger.warning(f"Could not create handoff from {from_role} to {to_role}: one or both agents not found")
        
        logger.info(f"Registered {len(self.handoff_definitions)} handoffs between agents")
    
    def list_available_teams(self) -> List[str]:
        """List all available team configurations.
        
        Returns:
            List of team keys from the teams.yaml configuration file
        """
        teams = set()
        
        # Add teams from global config
        if "teams" in self.teams_config:
            teams.update(self.teams_config["teams"].keys())
        
        return sorted(list(teams))
    
    @staticmethod
    def create_team(team_key: str, **kwargs) -> Team:
        """Convenience method to create a team from a configuration file.
        
        This is a static method that creates a singleton instance and delegates to it.
        
        Args:
            team_key: The key of the team in the configuration
            **kwargs: Additional arguments to override configuration values
            
        Returns:
            An initialized Team instance
        """
        return TeamBuilder.get_instance().create_team_from_config(team_key, **kwargs)
 