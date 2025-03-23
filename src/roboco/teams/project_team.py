"""
Project Team Module

This module defines the ProjectTeam class, which specializes in project creation
and management through a team of agents.
"""

from typing import Dict, Any, List, Optional
import os
from loguru import logger

from roboco.core.team import Team
from roboco.agents import HumanProxy
from roboco.agents.project_builder import ProjectBuilder


class ProjectTeam(Team):
    """
    A team consisting of a human proxy and a project agent.
    
    This team is specialized for project creation and management through
    natural language interactions.
    """
    
    def __init__(self, llm_config=None, workspace_dir="workspace", **kwargs):
        """
        Initialize the project team.
        
        Args:
            llm_config: Configuration for language models
            workspace_dir: Directory for workspace files
            **kwargs: Additional arguments to pass to the Team constructor
        """
        super().__init__(name="Project Team", **kwargs)
        
        # Store configuration
        self.llm_config = llm_config
        self.workspace_dir = workspace_dir
        
        # Initialize agents
        self._setup_agents()
        
        # Set up handoffs between agents
        self.register_handoffs()
    
    def _setup_agents(self):
        """Set up the agents for the team."""
        # Create the human proxy agent
        human = HumanProxy(
            name="APIUser",
            is_termination_msg=lambda x: "TERMINATE" in (x.get("content", "") or ""),
            human_input_mode="NEVER",  # No actual human input needed
            code_execution_config={"work_dir": self.workspace_dir, "use_docker": False}
        )
        
        # Create the project agent
        project_builder = ProjectBuilder(
            name="ProjectBuilder",
            llm_config=self.llm_config,
            workspace_dir=self.workspace_dir
        )
        
        # Add the agents to the team
        self.add_agent("human", human)
        self.add_agent("project_builder", project_builder)
    
    async def run_chat(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a chat session with the project agent.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the chat results
        """
        # Get the agents
        human = self.get_agent("human")
        project_builder = self.get_agent("project_builder")
        
        # Format the message
        message = f"""
        I'd like to create a new project based on the following idea:
        
        {query}
        
        Please analyze this request and create an appropriate project structure with:
        - A suitable name and description
        - The right teams assigned based on the nature of the project
        - An initial sprint with relevant tasks
        - A well-organized directory structure
        """
        
        # If teams were specified, add them to the message
        if teams:
            message += f"\n\nPlease assign the following teams: {', '.join(teams)}"
        
        # Start chat with the project agent
        await human.initiate_chat(
            project_builder,
            message=message,
        )
        
        # Get the chat history
        chat_history = human.chat_messages.get(project_builder, [])
        
        # Extract the response
        response = "No response received from the project agent."
        if chat_history and len(chat_history) > 1:
            response = chat_history[-1]["content"]
        
        return {
            "response": response,
            "chat_history": chat_history
        }
