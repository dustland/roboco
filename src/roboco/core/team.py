"""
Team Management Module

This module provides base classes for organizing agents into teams and managing their interactions.
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union

from loguru import logger

from autogen import (
    ConversableAgent,
    register_hand_off,
    AfterWork,
    AfterWorkOption,
    initiate_swarm_chat
)

from roboco.core.config import load_config, get_llm_config
from roboco.core.models import Task
from roboco.core.project_fs import ProjectFS

# Get a logger instance for this module
logger = logger.bind(module=__name__)

class Team(ABC):
    """
    Base class for all roboco teams, providing common functionality for team management.
    """
    
    def __init__(
        self,
        name: str,
        agents: Dict[str, ConversableAgent] = None,
        config_path: Optional[str] = None,
        fs: ProjectFS = None
    ):
        """Initialize a team of agents.
        
        Args:
            name: Name of the team
            agents: Dictionary of agents in the team (name -> agent)
            config_path: Optional path to team configuration file
        """
        self.name = name
        self.agents = agents or {}
        
        # Load configuration
        self.config = load_config(config_path)
        self.llm_config = get_llm_config(self.config)
        
        self.fs = fs
        
        # Storage for output artifacts
        self.artifacts = {}
        
        # Swarm configuration
        self.swarm_enabled = False
        self.shared_context = {}
        
        logger.info(f"Initialized Team: {name} with {len(self.agents)} agents")
    
    def add_agent(self, agent_name: str, agent: ConversableAgent) -> None:
        """Add an agent to the team."""
        self.agents[agent_name] = agent
    
    def get_agent(self, agent_name: str) -> Optional[ConversableAgent]:
        """Get an agent from the team by name."""
        return self.agents.get(agent_name)
    
    def create_agent(self, agent_class: type, name: str, **kwargs) -> ConversableAgent:
        """Create an agent with the given class and add it to the team."""
        # Ensure llm_config is set if not provided
        if 'llm_config' not in kwargs:
            kwargs['llm_config'] = self.llm_config
            
        # Create the agent
        agent = agent_class(name=name, **kwargs)
        
        # Add to the team
        self.add_agent(name, agent)
        
        return agent
    
    def save_artifact(self, name: str, content: Any, artifact_type: str = "text") -> str:
        """Save an artifact produced by the team."""
        artifact_id = f"{artifact_type}_{name}_{len(self.artifacts)}"
        self.artifacts[artifact_id] = {
            "name": name,
            "content": content,
            "type": artifact_type,
            "timestamp": "now"  # In real implementation, use actual timestamp
        }
        logger.info(f"Saved artifact {artifact_id}")
        return artifact_id
    
    def save_file_artifact(self, content: str, filename: str, directory: str = "outputs") -> str:
        """Save an artifact to a file on disk."""
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Save file
        file_path = os.path.join(directory, filename)
        with open(file_path, "w") as f:
            f.write(content)
            
        # Save as artifact too
        self.save_artifact(filename, content, artifact_type="file")
        
        logger.info(f"Saved file artifact to {file_path}")
        return file_path
    
    def _convert_to_dict(self, obj):
        """
        Convert potentially non-serializable objects to dictionaries.
        
        This method handles conversion of AutoGen's ChatResult and other complex objects
        into JSON-serializable dictionaries. It's used to ensure data can be properly
        serialized when saving results.
        
        Args:
            obj: Any object to convert
            
        Returns:
            A JSON-serializable equivalent
        """
        # Handle None
        if obj is None:
            return None
            
        # Handle basic types
        if isinstance(obj, (str, int, float, bool)):
            return obj
            
        # Handle lists
        if isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
            
        # Handle dictionaries
        if isinstance(obj, dict):
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
            
        # Handle ChatResult from AutoGen
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ChatResult':
            result = {}
            # Add the key attributes we know are commonly used
            for attr in ['chat_history', 'summary', 'cost', 'human_input']:
                if hasattr(obj, attr):
                    result[attr] = self._convert_to_dict(getattr(obj, attr))
            return result
            
        # Handle other objects with to_dict or dict methods
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return self._convert_to_dict(obj.to_dict())
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')):
            return self._convert_to_dict(obj.dict())
            
        # Last resort: convert to string
        try:
            return str(obj)
        except:
            return f"<Non-serializable object of type {type(obj).__name__}>"
    
    # ===== Swarm Management Methods =====
    
    def enable_swarm(self, shared_context: Optional[Dict[str, Any]] = None) -> None:
        """
        Enable swarm orchestration for this team.
        
        Args:
            shared_context: Initial shared context for the swarm (optional)
        """
        self.swarm_enabled = True
        self.shared_context = shared_context or {}
        logger.info("Swarm orchestration enabled for team")
    
    def register_handoffs(self) -> None:
        """
        Register handoffs between agents for swarm orchestration with task-specific logic.
        
        This method configures handoffs between agents based on their roles and the
        expected workflow, rather than creating a simple circular pattern.
        """
        if not self.swarm_enabled:
            self.enable_swarm()
            
        # Get all agents by name for role-based configuration
        agents_by_name = self.agents
        
        # Clear any existing handoffs first
        for agent in self.agents.values():
            if hasattr(agent, "_hand_to"):
                agent._hand_to = []
        
        # Define specific handoff logic based on agent roles
        handoffs = []
        
        # 1. Lead should hand off to Researcher to start the research process
        if "Lead" in agents_by_name and "Researcher" in agents_by_name:
            handoffs.append((agents_by_name["Lead"], agents_by_name["Researcher"]))
            logger.info("Registered: Lead → Researcher")
        
        # 2. Researcher should hand off to Developer when research is complete
        if "Researcher" in agents_by_name and "Developer" in agents_by_name:
            handoffs.append((agents_by_name["Researcher"], agents_by_name["Developer"]))
            logger.info("Registered: Researcher → Developer")
        
        # 3. Developer should hand off to Writer when implementation is complete
        if "Developer" in agents_by_name and "Writer" in agents_by_name:
            handoffs.append((agents_by_name["Developer"], agents_by_name["Writer"]))
            logger.info("Registered: Developer → Writer")
            
        # 4. Writer should hand off to Evaluator
        if "Writer" in agents_by_name and "Evaluator" in agents_by_name:
            handoffs.append((agents_by_name["Writer"], agents_by_name["Evaluator"]))
            logger.info("Registered: Writer → Evaluator")
            
        # 5. Evaluator should hand off to Lead to complete the cycle
        if "Evaluator" in agents_by_name and "Lead" in agents_by_name:
            handoffs.append((agents_by_name["Evaluator"], agents_by_name["Lead"]))
            logger.info("Registered: Evaluator → Lead")
            
        # Handle custom handoffs defined in the configuration
        if hasattr(self, "config") and hasattr(self.config, "teams"):
            team_config = getattr(self.config.teams, self.name, None)
            if team_config and hasattr(team_config, "workflow"):
                for handoff in team_config.workflow:
                    if "from" in handoff and "to" in handoff:
                        from_agent = agents_by_name.get(handoff["from"])
                        to_agent = agents_by_name.get(handoff["to"])
                        if from_agent and to_agent:
                            handoffs.append((from_agent, to_agent))
                            logger.info(f"Registered custom handoff: {handoff['from']} → {handoff['to']}")
        
        # Register all handoffs with appropriate conditions
        for from_agent, to_agent in handoffs:
            # Only hand off when the agent has something useful to contribute
            register_hand_off(
                agent=from_agent, 
                hand_to=[
                    AfterWork(
                        agent=to_agent,
                        # Only hand off if the agent has explicitly indicated handoff
                        condition=lambda msg: (
                            "I'll hand off to" in (msg.get("content", "") or "") or
                            "handing off to" in (msg.get("content", "") or "").lower() or
                            "RESEARCH_COMPLETE" in (msg.get("content", "") or "") or
                            "IMPLEMENTATION_COMPLETE" in (msg.get("content", "") or "") or
                            "EVALUATION_COMPLETE" in (msg.get("content", "") or "")
                        )
                    )
                ]
            )
        
        # Add explicit termination conditions for each agent
        for agent_name, agent in agents_by_name.items():
            # Set a conditional termination handler
            def create_termination_condition(agent_name):
                return lambda msg: (
                    "TASK_COMPLETE" in (msg.get("content", "") or "") or
                    "ALL_TASKS_COMPLETED" in (msg.get("content", "") or "") or
                    "TERMINATE" in (msg.get("content", "") or "")
                )
            
            agent.register_reply(
                [ConversableAgent], 
                lambda recipient, messages, sender, config: {
                    "content": "Task complete. Terminating swarm.",
                    "role": "assistant"
                },
                condition=create_termination_condition(agent_name)
            )
        
        logger.info(f"Registered {len(handoffs)} structured handoffs with conditional logic")
    
    def run_swarm(self, 
                initial_agent_name: str, 
                query: str, 
                context_variables: Optional[Dict[str, Any]] = None,
                max_rounds: int = 10) -> Dict[str, Any]:
        """
        Run a scenario using AG2's Swarm orchestration pattern.
        
        Args:
            initial_agent_name: Name of the agent to start the swarm
            query: The initial query to send to the swarm
            context_variables: Optional context variables to initialize the swarm with
            max_rounds: Maximum number of conversation rounds
            
        Returns:
            Dictionary containing the conversation history, context, and results
        """
        # Get the initial agent
        initial_agent = self.get_agent(initial_agent_name)
        if not initial_agent:
            raise ValueError(f"Agent {initial_agent_name} not found")
        
        # Prepare context variables
        context = context_variables or {}
        if self.shared_context:
            context.update(self.shared_context)
        
        # Get all agents
        all_agents = list(self.agents.values())
        
        # Run the swarm
        logger.info(f"Starting swarm with initial agent {initial_agent_name}")
        try:
            # initiate_swarm_chat returns a tuple of (chat_result, context_variables, last_agent)
            chat_result = initiate_swarm_chat(
                initial_agent=initial_agent,
                agents=all_agents,
                messages=[{"role": "user", "content": query}],
                context_variables=context,
                max_rounds=max_rounds,
                after_work=AfterWorkOption.TERMINATE
            )
            
            # Update the team's shared context with the results from the swarm
            if isinstance(chat_result, tuple) and len(chat_result) > 1:
                updated_context = chat_result[1]
                self.shared_context.update(updated_context)
                
                # Prepare the result with converted chat_result to ensure JSON serialization
                result = {
                    "chat_result": self._convert_to_dict(chat_result[0]),
                    "context": self._convert_to_dict(updated_context),
                    "messages": self._convert_to_dict(chat_result[0].chat_history) if hasattr(chat_result[0], 'chat_history') else []
                }
                
                if len(chat_result) > 2:
                    result["last_agent"] = chat_result[2].name
            else:
                # Handle case where chat_result is not a tuple
                result = {
                    "chat_result": self._convert_to_dict(chat_result),
                    "messages": self._convert_to_dict(getattr(chat_result, 'chat_history', [])) if hasattr(chat_result, 'chat_history') else []
                }
                
            return result
            
        except Exception as e:
            import traceback
            import sys
            error_tb = traceback.format_exc()
            
            # Log detailed agent information
            agent_details = []
            for agent_name, agent in self.agents.items():
                model_info = "unknown"
                if hasattr(agent, "llm_config") and agent.llm_config:
                    model_info = agent.llm_config.get("model", "unknown")
                    api_type = agent.llm_config.get("api_type", "unknown")
                    base_url = agent.llm_config.get("base_url", "N/A")
                    model_info = f"{model_info} ({api_type}, {base_url})"
                
                agent_details.append(f"  - {agent_name}: {model_info}")
            
            agent_info = "\n".join(agent_details)
            
            logger.error(f"Error in swarm execution: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Initial agent: {initial_agent_name}")
            logger.error(f"Team agents and models:\n{agent_info}")
            logger.error(f"Traceback: {error_tb}")
            
            # Return detailed error information
            return {
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_tb,
                "initial_agent": initial_agent_name,
                "agents": {name: getattr(agent, "llm_config", {}).get("model", "unknown") 
                          for name, agent in self.agents.items()}
            }

    def add_to_context(self, key: str, value: Any) -> None:
        """
        Add a key-value pair to the team's shared context.
        
        Args:
            key: The key to add
            value: The value to associate with the key
        """
        self.shared_context[key] = value
        logger.info(f"Added {key} to team's shared context")
        
        # Enable swarm if not already enabled
        if not self.swarm_enabled:
            self.enable_swarm()
            
    def set_output_dir(self, output_dir: str) -> None:
        """
        Set the output directory for the team.
        
        Args:
            output_dir: The output directory path
        """
        self.add_to_context("output_dir", output_dir)
        logger.info(f"Set team output directory to {output_dir}")
