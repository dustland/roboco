"""
Team Builder Module

This module provides a builder pattern for creating teams with different agent compositions
based on role configurations. It simplifies the process of creating and configuring teams.
"""

import os
from typing import Dict, Any, List, Optional, Type, Set, Union
from loguru import logger

from roboco.core.team import Team
from roboco.core.agent import Agent
from roboco.core.agent_factory import AgentFactory
from roboco.core.tool import Tool

class TeamBuilder:
    """Builder for creating teams with different agent compositions."""
    
    def __init__(
        self,
        use_specialized_agents: bool = True,
        **agent_factory_kwargs
    ):
        """Initialize the team builder.
        
        Args:
            use_specialized_agents: Whether to use specialized agent classes when available
            **agent_factory_kwargs: Additional keyword arguments to pass to the AgentFactory
        """
        self.use_specialized_agents = use_specialized_agents
        
        # Create agent factory with specialized agents if requested
        self.agent_factory = AgentFactory(
            register_specialized_agents=use_specialized_agents,
            **agent_factory_kwargs
        )
        
        # Initialize collections
        self.selected_roles: List[str] = []
        self.tools: Dict[str, List[Tool]] = {}
        self.agent_configs: Dict[str, Dict[str, Any]] = {}
        self.handoff_definitions: List[Dict[str, Any]] = []
        self.tool_executor_role: Optional[str] = None
    
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
        
        # Create initial team instance
        team = team_class(name=name, agents={}, **team_kwargs)
        
        # Enable swarm orchestration
        team.enable_swarm()
        
        # Create all agents from selected roles
        agents = {}
        for role_key in self.selected_roles:
            # Get agent-specific configs
            agent_kwargs = self.agent_configs.get(role_key, {})
            
            # Create the agent
            agent = self.agent_factory.create_agent(
                role_key=role_key,
                tools=self.tools.get(role_key, []),
                **agent_kwargs
            )
            
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
 