"""
Team Manager Module

This module provides functionality for managing teams, including building teams with
different agent compositions, assigning appropriate teams for tasks, and
configuring team behaviors and handoffs.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Type, Set, Union
from loguru import logger

from roboco.core.team import Team
from roboco.core.agent import Agent
from roboco.core.agent_factory import AgentFactory
from roboco.core.tool import Tool
from roboco.core.models.task import Task
from roboco.core.project_fs import ProjectFS

from roboco.tools.fs import FileSystemTool
from roboco.tools.browser_use import BrowserUseTool
from roboco.teams.versatile import VersatileTeam
from roboco.teams.planning import PlanningTeam

# Initialize logger
logger = logger.bind(module=__name__)


class TeamManager:
    """
    Manager for building, configuring, and assigning teams.
    
    This class combines the functionality of TeamBuilder and TeamAssigner
    into a single unified interface. It provides methods for creating
    teams with different agent compositions and assigning teams to tasks.
    """
    
    def __init__(
        self,
        fs: ProjectFS,
        teams_config_path: str = "config/teams.yaml",
        **agent_factory_kwargs
    ):
        """Initialize the team manager.
        
        Args:
            teams_config_path: Path to the teams configuration file (YAML)
            fs: Optional ProjectFS instance
            **agent_factory_kwargs: Additional keyword arguments to pass to the AgentFactory
        """
        # Get the singleton AgentFactory instance
        self.agent_factory = AgentFactory.get_instance(**agent_factory_kwargs)
        
        # Store the file system reference
        self.fs = fs
        
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
        
        # Simple mapping of task keywords to team types
        self.task_team_mapping = {
            "research": "research",
            "planning": "planning",
            "design": "design",
            "development": "development",
            "implementation": "development",
            "testing": "testing",
            "deployment": "deployment",
            "general": "versatile",
            "universal": "versatile",
            "common": "versatile",
            "miscellaneous": "versatile",
            "other": "versatile",
            "versatile": "versatile"
        }
    
    # --- Methods from TeamBuilder ---
    
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
    
    def with_roles(self, *role_keys: str) -> 'TeamManager':
        """Select the roles to include in the team.
        
        Args:
            *role_keys: Keys of the roles to include
            
        Returns:
            The builder instance for method chaining
        """
        self.selected_roles = list(role_keys)
        return self
    
    def with_tool_executor(self, role_key: str = "human_proxy") -> 'TeamManager':
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
    
    def with_tools(self, role_key: str, tools: List[Tool]) -> 'TeamManager':
        """Add tools to a specific role.
        
        Args:
            role_key: Key of the role to add tools to
            tools: List of tools to add
            
        Returns:
            The builder instance for method chaining
        """
        self.tools[role_key] = tools
        return self
    
    def with_agent_config(self, role_key: str, **kwargs) -> 'TeamManager':
        """Configure specific parameters for an agent.
        
        Args:
            role_key: Key of the role to configure
            **kwargs: Configuration parameters for the agent
            
        Returns:
            The builder instance for method chaining
        """
        self.agent_configs[role_key] = kwargs
        return self
    
    def with_handoff(self, from_role: str, to_role: str, condition: Optional[Dict[str, Any]] = None) -> 'TeamManager':
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
    
    def with_circular_workflow(self, *role_keys: str) -> 'TeamManager':
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
        builder = TeamManager()
        
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
        
        # Configure agent settings
        if "agent_settings" in team_config:
            for role, settings in team_config["agent_settings"].items():
                builder.with_agent_config(role, **settings)
        
        # Configure handoffs
        if "handoffs" in team_config:
            for handoff in team_config["handoffs"]:
                builder.with_handoff(
                    handoff["from"],
                    handoff["to"],
                    handoff.get("condition")
                )
        
        # Configure team class
        team_class = Team
        if "team_class" in team_config:
            team_class_name = team_config["team_class"]
            # Import the team class dynamically
            if team_class_name == "PlanningTeam":
                team_class = PlanningTeam
            elif team_class_name == "VersatileTeam":
                team_class = VersatileTeam
        
        # Build the team
        return builder.build(team_class=team_class, name=team_config.get("name"))
    
    def build(self, team_class: Type[Team] = Team, name: str = None, **team_kwargs) -> Team:
        """Build a team with the configured roles and agents.
        
        Args:
            team_class: The Team class to instantiate
            name: Optional name for the team
            **team_kwargs: Additional team constructor arguments
            
        Returns:
            An initialized Team instance
        """
        # Create the team
        name = name or "CustomTeam"
        team = team_class(name=name, **team_kwargs)
        
        # Create and add agents with roles
        for role_key in self.selected_roles:
            # Get agent configuration if available
            agent_config = self.agent_configs.get(role_key, {})
            
            # Create and add the agent to the team
            agent = self.agent_factory.create_agent(role_key=role_key, **agent_config)
            team.add_agent(role_key, agent)
            
            # Register tools with the agent if specified
            if role_key in self.tools:
                for tool in self.tools[role_key]:
                    tool.register_with_agents(agent)
        
        # Register handoffs if specified
        self._register_handoffs(team)
        
        return team
    
    def _register_handoffs(self, team: Team) -> None:
        """Register agent handoffs with a team.
        
        Args:
            team: The team to register handoffs with
        """
        # Import needed dependencies here to avoid circular imports
        try:
            from autogen import register_hand_off, OnCondition, AfterWork
        except ImportError:
            logger.warning("AutoGen not available, handoffs not registered")
            return
        
        for handoff in self.handoff_definitions:
            from_role = handoff["from_role"]
            to_role = handoff["to_role"]
            condition = handoff["condition"]
            
            # Get the agents
            from_agent = team.get_agent(from_role)
            to_agent = team.get_agent(to_role) if to_role else None
            
            if from_agent and to_agent:
                # Create the condition if specified
                if condition:
                    # Convert the condition to an OnCondition object
                    on_condition = OnCondition(
                        condition=lambda agent, messages, **condition_params: (
                            condition["function"](agent, messages, **condition_params)
                        ),
                        target=to_agent
                    )
                    register_hand_off(from_agent, on_condition)
                else:
                    # Simple handoff with no condition
                    register_hand_off(from_agent, to_agent)
    
    def list_available_teams(self) -> List[str]:
        """List all available teams from the configuration.
        
        Returns:
            List of team keys
        """
        teams = []
        if "teams" in self.teams_config:
            teams = list(self.teams_config["teams"].keys())
        return teams
    
    @staticmethod
    def create_team(team_key: str, **kwargs) -> Team:
        """Create a team of the specified type with default configuration.
        
        Args:
            team_key: Key of the team to create
            **kwargs: Additional arguments for the team
            
        Returns:
            Initialized team instance
        """
        # Create a new TeamManager to handle this request
        team_manager = TeamManager()
        return team_manager.create_team_from_config(team_key, **kwargs)
    
    # --- Methods from TeamAssigner ---
    
    def set_fs(self, fs: ProjectFS) -> None:
        """Set the project filesystem.
        
        Args:
            fs: ProjectFS instance
        """
        self.fs = fs
    
    def get_team_for_task(self, task: Task) -> Any:
        """Get an appropriate team for executing the given task.
        
        Args:
            task: The task to get a team for
            
        Returns:
            A team instance appropriate for the task
        """
        # Determine the team type based on the task
        description = task.description.lower()
        team_type = self._determine_team_type(description)
        
        return self._create_team(team_type)
    
    def get_team_for_tasks(self, tasks: List[Task]) -> Any:
        """Get an appropriate team for executing a group of tasks.
        
        Args:
            tasks: The tasks to get a team for
            
        Returns:
            A team instance appropriate for the tasks
        """
        if tasks:
            return self.get_team_for_task(tasks[0])
        
        # Default to versatile team if no tasks provided
        return self._create_team("versatile")
    
    def _determine_team_type(self, description: str) -> str:
        """Determine the appropriate team type for a description.
        
        Args:
            description: Description of the task or phase
            
        Returns:
            The determined team type as a string
        """
        # Look for keywords in the description
        for keyword, team_type in self.task_team_mapping.items():
            if keyword in description:
                logger.debug(f"Determined team type '{team_type}' for description '{description}'")
                return team_type
        
        # Default to versatile team if no specific match found
        logger.debug(f"No specific team type found for description '{description}', defaulting to versatile")
        return "versatile"
    
    def _create_team(self, team_type: str) -> Any:
        """Create and configure a team of the specified type.
        
        Args:
            team_type: Type of team to create
            
        Returns:
            A team instance appropriate for the team type
        """
        if not self.fs:
            logger.warning("No filesystem specified, team might not function correctly")
        
        logger.debug(f"Creating team of type '{team_type}'")
        
        if team_type == "planning":
            return PlanningTeam(fs=self.fs)
        else:
            # Default to VersatileTeam for better adaptability
            return VersatileTeam(fs=self.fs) 