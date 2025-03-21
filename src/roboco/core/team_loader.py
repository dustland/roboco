"""
Team Loader Module

This module provides functionality to load and create teams from configuration files.
It supports both global team configurations and team-specific configurations.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Type, Set, Union
from loguru import logger

from roboco.core.team import Team
from roboco.core.team_builder import TeamBuilder
from roboco.tools.fs import FileSystemTool
from roboco.tools.browser_use import BrowserUseTool

class TeamLoader:
    """Loader for creating teams from configuration files."""
    
    def __init__(
        self,
        teams_config_path: str = "config/teams.yaml",
        teams_dir: str = "config/teams",
        use_specialized_agents: bool = True,
        agent_factory_kwargs: Optional[Dict[str, Any]] = None
    ):
        """Initialize the team loader.
        
        Args:
            teams_config_path: Path to the global teams configuration file
            teams_dir: Directory containing team-specific configuration files
            use_specialized_agents: Whether to use specialized agent classes when available
            agent_factory_kwargs: Additional keyword arguments to pass to the AgentFactory
        """
        self.teams_config_path = teams_config_path
        self.teams_dir = teams_dir
        self.use_specialized_agents = use_specialized_agents
        self.agent_factory_kwargs = agent_factory_kwargs or {}
        
        # Create the base team builder, delegating agent creation details to AgentFactory
        self.team_builder = TeamBuilder(
            use_specialized_agents=use_specialized_agents,
            **self.agent_factory_kwargs
        )
        
        # Load the teams configuration
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
    
    def configure_builder_from_config(self, team_config: Dict[str, Any]) -> TeamBuilder:
        """Configure a team builder based on a team configuration.
        
        Args:
            team_config: The team configuration dictionary
            
        Returns:
            A configured TeamBuilder instance
        """
        # Create a new builder using our base configuration
        builder = TeamBuilder(
            use_specialized_agents=self.use_specialized_agents,
            **self.agent_factory_kwargs
        )
        
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
        
        return builder
    
    def create_team(self, team_key: str, **kwargs) -> Team:
        """Create a team based on its configuration.
        
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
        
        # Configure the builder
        builder = self.configure_builder_from_config(team_config)
        
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