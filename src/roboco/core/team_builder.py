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
        teams_dir: str = "config/teams",
        **agent_factory_kwargs
    ):
        """Initialize the team builder.
        
        Args:
            teams_config_path: Path to the global teams configuration file
            teams_dir: Directory containing team-specific configuration files
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
        self.teams_dir = teams_dir
        self.teams_config = self._load_teams_config(teams_config_path)
        
        # Initialize available tools
        self.available_tools = {
            "filesystem": lambda: FileSystemTool(),
            "browser_use": lambda: BrowserUseTool()
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
    
    def _load_team_specific_config(self, team_key: str) -> Optional[Dict[str, Any]]:
        """Load a team-specific configuration from a YAML file.
        
        Args:
            team_key: The key of the team to load the configuration for
            
        Returns:
            The team-specific configuration, or None if the file doesn't exist
        """
        file_path = os.path.join(self.teams_dir, f"{team_key}.yaml")
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"Loaded team-specific configuration from {file_path}")
                return config
        except Exception as e:
            logger.warning(f"No team-specific config found at {file_path}: {str(e)}")
            return None
    
    def get_team_config(self, team_key: str) -> Dict[str, Any]:
        """Get the configuration for a specific team.
        
        Combines the global team configuration with any team-specific configuration.
        
        Args:
            team_key: The key of the team in the configuration
            
        Returns:
            The combined team configuration
        """
        # Start with the global configuration
        try:
            team_config = self.teams_config["teams"][team_key].copy()
        except (KeyError, TypeError):
            logger.warning(f"Team '{team_key}' not found in global config, using empty configuration")
            team_config = {}
        
        # Add any team-specific configuration, overriding global settings
        specific_config = self._load_team_specific_config(team_key)
        if specific_config:
            team_config.update(specific_config)
        
        return team_config
    
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
        
        # Configure agent-specific settings
        if "agent_configs" in team_config:
            for role_key, config in team_config["agent_configs"].items():
                builder.with_agent_config(role_key, **config)
        
        # Configure tools
        if "tools" in team_config:
            for tool_key in team_config["tools"]:
                if tool_key in self.available_tools:
                    # Create the tool instance
                    tool = self.available_tools[tool_key]()
                    
                    # Register with all roles (will be filtered by tool executor)
                    for role_key in team_config.get("roles", []):
                        if role_key != team_config.get("tool_executor"):
                            if role_key not in builder.tools:
                                builder.tools[role_key] = []
                            builder.tools[role_key].append(tool)
        
        # Configure workflow/handoffs
        if "workflow" in team_config:
            for handoff in team_config["workflow"]:
                builder.with_handoff(
                    from_role=handoff["from"],
                    to_role=handoff["to"],
                    condition=handoff.get("condition")
                )
        
        # Build the team
        team = builder.build(
            name=team_config.get("name", f"Team_{team_key}"),
            description=team_config.get("description", "")
        )
        
        # Set output directory if specified
        if "output_dir" in team_config:
            output_dir = team_config["output_dir"]
            os.makedirs(output_dir, exist_ok=True)
            team.shared_context["output_dir"] = output_dir
        
        logger.info(f"Created team '{team.name}' with {len(team.agents)} agents")
        return team
    
    def build(self, team_class: Type[Team] = Team, name: str = None, **team_kwargs) -> Team:
        """Build the team with the configured agents.
        
        Args:
            team_class: The team class to instantiate
            name: Name for the team (default: Generated based on roles)
            **team_kwargs: Additional arguments for the team constructor
            
        Returns:
            An initialized team instance
        """
        # Generate a name if not provided
        if name is None:
            name = "Team_" + "_".join(self.selected_roles)
        
        # Debug: Print selected roles
        logger.debug(f"Building team with selected roles: {self.selected_roles}")
        
        # Remove description if present (not supported by Team constructor)
        description = team_kwargs.pop("description", None)
        if description:
            logger.debug(f"Team description: {description}")
            
        # Create initial team instance
        team = team_class(name=name, agents={}, **team_kwargs)
        
        # Enable swarm orchestration
        team.enable_swarm()
        
        # Create all agents from selected roles
        agents = {}
        for role_key in self.selected_roles:
            # Get agent-specific configs
            agent_kwargs = self.agent_configs.get(role_key, {})
            logger.debug(f"Creating agent for role '{role_key}' with kwargs: {agent_kwargs}")
            
            # Check if we have a specialized agent class registered for this role
            if role_key in self.agent_factory.agent_registry:
                logger.info(f"Using specialized agent class for role '{role_key}': {self.agent_factory.agent_registry[role_key].__name__}")
            
            # Create the agent using the factory
            agent = self.agent_factory.create_agent(
                role_key=role_key,
                tools=self.tools.get(role_key, []),
                **agent_kwargs
            )
            
            logger.info(f"Created agent for role '{role_key}' with type: {type(agent).__name__}")
            
            # Add to our collection
            agents[agent.name] = agent
            
            # Add to the team
            team.add_agent(agent.name, agent)
            logger.info(f"Added agent '{agent.name}' of type {agent.__class__.__name__} to the team")
        
        # Register tools with the tool executor if specified
        if self.tool_executor_role:
            # Get the role name from the agent factory's configuration
            tool_executor_name = None
            try:
                tool_executor_name = self.agent_factory.roles_config["roles"][self.tool_executor_role]["name"]
            except (KeyError, TypeError):
                # If we can't find it in the config, try to find it by looking at agent names
                for agent_name, agent in agents.items():
                    system_message = getattr(agent, "system_message", "").lower()
                    if (self.tool_executor_role in agent_name.lower() or 
                        (system_message and self.tool_executor_role in system_message)):
                        tool_executor_name = agent_name
                        break
            
            if tool_executor_name and tool_executor_name in team.agents:
                tool_executor = team.get_agent(tool_executor_name)
                
                for agent_name, agent in agents.items():
                    if agent != tool_executor:
                        # Register any tools the agent has with the tool executor
                        for tool_name, tool in agent.function_map.items():
                            if hasattr(tool, "register_with_agents") and callable(tool.register_with_agents):
                                tool.register_with_agents(agent, tool_executor)
        
        # Register handoffs
        if self.handoff_definitions:
            from autogen import register_hand_off, AfterWork
            
            for handoff in self.handoff_definitions:
                from_role_name = None
                to_role_name = None
                
                # Get role names from agent factory configuration
                try:
                    from_role_name = self.agent_factory.roles_config["roles"][handoff["from_role"]]["name"]
                    to_role_name = self.agent_factory.roles_config["roles"][handoff["to_role"]]["name"]
                except (KeyError, TypeError):
                    # If we can't find it in the config, try to find matching agents
                    for agent_name, agent in agents.items():
                        system_message = getattr(agent, "system_message", "").lower()
                        if (handoff["from_role"] in agent_name.lower() or 
                            (system_message and handoff["from_role"] in system_message)):
                            from_role_name = agent_name
                        
                        if (handoff["to_role"] in agent_name.lower() or 
                            (system_message and handoff["to_role"] in system_message)):
                            to_role_name = agent_name
                
                if from_role_name in team.agents and to_role_name in team.agents:
                    from_agent = team.get_agent(from_role_name)
                    to_agent = team.get_agent(to_role_name)
                    
                    # Create the handoff
                    register_hand_off(
                        agent=from_agent,
                        hand_to=AfterWork(agent=to_agent)
                    )
                else:
                    logger.warning(f"Could not create handoff from {handoff['from_role']} to {handoff['to_role']}: agent not found")
            
            logger.info(f"Registered {len(self.handoff_definitions)} handoffs between agents")
        
        return team
    
    def list_available_teams(self) -> List[str]:
        """List all available team configurations.
        
        Returns:
            List of team keys from global and team-specific configurations
        """
        teams = set()
        
        # Add teams from global config
        if "teams" in self.teams_config:
            teams.update(self.teams_config["teams"].keys())
        
        # Add teams from team-specific configs
        if os.path.exists(self.teams_dir):
            for filename in os.listdir(self.teams_dir):
                if filename.endswith(".yaml"):
                    team_key = filename[:-5]  # Remove .yaml
                    teams.add(team_key)
        
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
 