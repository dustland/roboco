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


class Team(ABC):
    """
    Base class for all roboco teams, providing common functionality for team management.
    """
    
    def __init__(
        self,
        name: str,
        agents: Dict[str, ConversableAgent] = None,
        config_path: Optional[str] = None
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
        
        # Storage for output artifacts
        self.artifacts = {}
        
        # Swarm configuration
        self.swarm_enabled = False
        self.shared_context = {}
        
        logger.info(f"Initialized Team: {name} with {len(self.agents)} agents")
    
    def add_agent(self, agent_name: str, agent: ConversableAgent) -> None:
        """Add an agent to the team."""
        self.agents[agent_name] = agent
        logger.info(f"Added agent '{agent_name}' to the team")
    
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
        Register handoffs between agents for swarm orchestration.
        
        This method configures the handoff conditions between agents using AfterWork,
        allowing for automatic transitions during a swarm chat.
        """
        if not self.swarm_enabled:
            self.enable_swarm()
            
        # Create circular handoffs between all agents
        agent_list = list(self.agents.values())
        if len(agent_list) >= 2:
            for i, agent in enumerate(agent_list):
                next_agent = agent_list[(i + 1) % len(agent_list)]
                register_hand_off(
                    agent=agent,
                    hand_to=[AfterWork(agent=next_agent)]
                )
            
        logger.info(f"Registered handoffs between {len(agent_list)} agents")
    
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
                messages=[query],
                context_variables=context,
                max_rounds=max_rounds,
                after_work=AfterWorkOption.TERMINATE
            )
            
            # Update the team's shared context with the results from the swarm
            if isinstance(chat_result, tuple) and len(chat_result) > 1:
                updated_context = chat_result[1]
                self.shared_context.update(updated_context)
                
                # Prepare the result
                result = {
                    "chat_result": chat_result[0],
                    "context": updated_context
                }
                
                if len(chat_result) > 2:
                    result["last_agent"] = chat_result[2].name
            else:
                # Handle case where chat_result is not a tuple
                result = {"chat_result": chat_result}
                
            return result
            
        except Exception as e:
            logger.error(f"Error in swarm execution: {str(e)}")
            return {"error": str(e)}


class BaseExecutionTeam(Team):
    """Base class for teams that execute tasks."""
    
    def __init__(
        self, 
        name: str,
        project_dir: str, 
        agent_types: List[str], 
        tool_types: List[str],
        config_path: Optional[str] = None
    ):
        """Initialize the execution team.
        
        Args:
            name: Name of the team
            project_dir: Directory of the project
            agent_types: List of agent types to include in the team
            tool_types: List of tools to make available to the team
            config_path: Optional path to team configuration file
        """
        super().__init__(name=name, config_path=config_path)
        self.project_dir = project_dir
        self.agent_types = agent_types
        self.tool_types = tool_types
        
        # Initialize agents based on agent_types
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize the agents for this team."""
        for agent_type in self.agent_types:
            agent = self._create_agent(agent_type)
            if agent:
                self.add_agent(agent_type, agent)
    
    def _create_agent(self, agent_type: str) -> Optional[ConversableAgent]:
        """Create an agent of the specified type.
        
        Args:
            agent_type: Type of agent to create
            
        Returns:
            An initialized agent instance
        """
        # This would be implemented with a factory pattern
        # For now, we'll just log and return None
        logger.info(f"Creating agent of type: {agent_type}")
        return None
    
    @abstractmethod
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute the given tasks using this team's agents.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Dictionary with execution results
        """
        pass


class SequentialExecutionTeam(BaseExecutionTeam):
    """Team that executes tasks sequentially."""
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks in sequence."""
        results = {
            "tasks": [],
            "success": True,
            "execution_time": 0
        }
        
        for task in tasks:
            # Skip completed tasks
            if task.status == "DONE":
                results["tasks"].append({
                    "description": task.description,
                    "status": "DONE",
                    "skipped": True
                })
                continue
            
            # Execute task (placeholder)
            logger.info(f"SequentialTeam executing task: {task.description}")
            
            # Record result (placeholder)
            results["tasks"].append({
                "description": task.description,
                "status": "DONE",
                "execution_time": 0,
                "output": f"Executed task: {task.description}",
                "error": None
            })
        
        return results


class ParallelExecutionTeam(BaseExecutionTeam):
    """Team that executes tasks in parallel."""
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks in parallel."""
        results = {
            "tasks": [],
            "success": True,
            "execution_time": 0
        }
        
        # Placeholder for parallel execution
        logger.info(f"ParallelTeam would execute {len(tasks)} tasks in parallel")
        
        for task in tasks:
            results["tasks"].append({
                "description": task.description,
                "status": "DONE",
                "execution_time": 0,
                "output": f"Executed task: {task.description}",
                "error": None
            })
        
        return results


class IterativeExecutionTeam(BaseExecutionTeam):
    """Team that executes tasks iteratively with feedback loops."""
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks iteratively."""
        results = {
            "tasks": [],
            "success": True,
            "execution_time": 0
        }
        
        # Placeholder for iterative execution
        logger.info(f"IterativeTeam would execute {len(tasks)} tasks iteratively")
        
        for task in tasks:
            results["tasks"].append({
                "description": task.description,
                "status": "DONE",
                "execution_time": 0,
                "output": f"Executed task: {task.description}",
                "error": None
            })
        
        return results


class GenericExecutionTeam(BaseExecutionTeam):
    """Generic team for when no specialized team is available."""
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks with a generic approach."""
        results = {
            "tasks": [],
            "success": True,
            "execution_time": 0
        }
        
        # Placeholder for generic execution
        logger.info(f"GenericTeam executing {len(tasks)} tasks")
        
        for task in tasks:
            results["tasks"].append({
                "description": task.description,
                "status": "DONE",
                "execution_time": 0,
                "output": f"Executed task: {task.description}",
                "error": None
            })
        
        return results
