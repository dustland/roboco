"""
Project Team Module

This module defines the ProjectTeam class, which specializes in project creation
and management through a team of agents.
"""

from typing import Dict, Any, List, Optional
import os
from loguru import logger
import asyncio
import json

from roboco.core.agent import Agent
from roboco.agents.project_builder import ProjectBuilder


class PlanningTeam:
    """Team for creating and managing projects."""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """Initialize the project team.
        
        Args:
            workspace_dir: Directory for workspace files
        """
        self.workspace_dir = workspace_dir
        
        # Create the agents
        from roboco.agents.human_proxy import HumanProxy
        
        # Initialize the agents
        executer = Agent(
            name="executer",
            system_message="""You are an execution agent that helps prepare projects.
            """,
            human_input_mode="NEVER",
            terminate_msg="TERMINATE",
            llm_config=False,
            code_execution_config={"work_dir": f"{workspace_dir}/code", "use_docker": False}
        )
        project_builder = ProjectBuilder(
            name="project_builder",
            terminate_msg=None,  # Set to None to prevent premature conversation termination
        )
        self.agents = {
            "executer": executer,
            "project_builder": project_builder
        }
        
        # Register tools with agents
        from roboco.tools.fs import FileSystemTool
        fs_tool = FileSystemTool()

        fs_tool.register_with_agents(project_builder, executer)
        
    def get_agent(self, name: str) -> Agent:
        """Get an agent by name.
        
        Args:
            name: Name of the agent
            
        Returns:
            The agent
            
        Raises:
            ValueError: If the agent is not found
        """
        if name not in self.agents:
            raise ValueError(f"Agent '{name}' not found")
        return self.agents[name]
    
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
        executer = self.get_agent("executer")
        project_builder = self.get_agent("project_builder")
        
        # Format the message to leverage the LLM's capabilities for project structure creation
        message = f"""
I'd like to create a new project based on the following idea:

{query}

Please analyze this request and create an appropriate project structure with:
- A well-organized directory structure that follows best practices for this type of project
- All necessary files including configuration files, README, and initial code files
- Appropriate file content that provides a solid starting point for development

Create a workspace directory if it doesn't exist, and then create the project within it.
Use the FileSystemTool to create the necessary directories and files.

Focus on creating a comprehensive project structure that would be ready for immediate development.
        """
        
        # If teams were specified, add them to the message
        if teams:
            message += f"\n\nPlease assign the following teams: {', '.join(teams)}"
        
        try:
            # Start chat with the project agent and get the result directly
            chat_result = executer.initiate_chat(
                recipient=project_builder,
                message=message,
                max_turns=10,
            )
            
            # Return the chat results
            return {
                "response": chat_result.summary,
                "chat_history": chat_result.chat_history
            }
            
        except Exception as e:
            logger.error(f"Error in project chat: {str(e)}")
            return {
                "error": str(e)
            }
