"""
Project Team Module

This module defines the ProjectTeam class, which specializes in project creation
and management through a team of agents.
"""

from typing import Dict, Any, List, Optional
import os
import json
from datetime import datetime
from loguru import logger
import asyncio

from roboco.core.agent import Agent
from roboco.agents.planner import Planner
from roboco.core.models import ProjectManifest


class PlanningTeam:
    """Team for creating and managing projects."""
    
    def __init__(self, workspace_dir: str = "workspace"):
        """Initialize the project team.
        
        Args:
            workspace_dir: Directory for workspace files
        """
        self.workspace_dir = workspace_dir
        
        # Create necessary directories
        self.src_dir = os.path.join(workspace_dir, "src")
        self.docs_dir = os.path.join(workspace_dir, "docs")
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        
        # Create the agents
        from roboco.agents.human_proxy import HumanProxy
        
        # Initialize the agents
        executer = Agent(
            name="executer",
            system_message="""You are an execution agent that helps prepare projects.
            When creating files, always put source code in the src directory and documentation in the docs directory.
            """,
            human_input_mode="NEVER",
            terminate_msg="TERMINATE",
            llm_config=False,
            code_execution_config={"work_dir": self.workspace_dir, "use_docker": False}
        )
        planner = Planner(
            name="planner",
            terminate_msg=None,  # Set to None to prevent premature conversation termination
        )
        self.agents = {
            "executer": executer,
            "planner": planner
        }
        
        # Register tools with agents
        from roboco.tools.fs import FileSystemTool
        fs_tool = FileSystemTool()

        fs_tool.register_with_agents(planner, executer)
        
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
    
    async def generate_project_manifest(self, query: str, teams: Optional[List[str]] = None) -> ProjectManifest:
        """
        Generate a project manifest based on the user's query.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            ProjectManifest object
        """
        # Get the agents
        executer = self.get_agent("executer")
        planner = self.get_agent("planner")
        
        # Format the message to generate a project manifest
        message = f"""
I need you to create a project manifest for the following project idea:

{query}

Please provide a structured JSON manifest with the following fields:
- name: A concise, descriptive name for the project
- description: A detailed description of the project
- directory_name: A clean, normalized folder name (use snake_case, no spaces, lowercase)
- structure: An object describing the project's structure
- folder_structure: Array of subdirectories to create (always include "src" and "docs")
- meta: Additional metadata that might be useful

The JSON should be valid and properly formatted. This manifest will be used to organize the project files.
If the project involves specific technologies or frameworks, include those details in the manifest.

ONLY OUTPUT THE JSON, nothing else.
        """
        
        # If teams were specified, add them to the message
        if teams:
            message += f"\n\nPlease consider these teams in your planning: {', '.join(teams)}"
        
        try:
            # Get manifest data from the planner
            chat_result = executer.initiate_chat(
                recipient=planner,
                message=message,
                max_turns=5,
            )
            
            # Extract JSON from the response
            manifest_text = chat_result.summary.strip()
            
            # Remove any markdown code block formatting if present
            if manifest_text.startswith("```json"):
                manifest_text = manifest_text.split("```json", 1)[1]
            if manifest_text.startswith("```"):
                manifest_text = manifest_text.split("```", 1)[1]
            if manifest_text.endswith("```"):
                manifest_text = manifest_text.rsplit("```", 1)[0]
                
            manifest_text = manifest_text.strip()
            
            # Parse JSON
            manifest_data = json.loads(manifest_text)
            
            # Ensure required fields are present
            manifest_data.setdefault("folder_structure", ["src", "docs"])
            if "src" not in manifest_data["folder_structure"]:
                manifest_data["folder_structure"].append("src")
            if "docs" not in manifest_data["folder_structure"]:
                manifest_data["folder_structure"].append("docs")
                
            manifest_data.setdefault("created_at", datetime.now().isoformat())
            manifest_data.setdefault("task_file", "tasks.md")
            
            # Create manifest object
            manifest = ProjectManifest(**manifest_data)
            
            # Save manifest to file for reference
            manifest_path = os.path.join(self.workspace_dir, f"{manifest.directory_name}_manifest.json")
            with open(manifest_path, "w") as f:
                f.write(json.dumps(manifest_data, indent=2))
                
            return manifest
            
        except Exception as e:
            logger.error(f"Error generating project manifest: {str(e)}")
            # Create a default manifest as fallback
            clean_name = "".join(c.lower() if c.isalnum() else "_" for c in query[:30])
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            return ProjectManifest(
                name=f"Project from query",
                description=query,
                directory_name=f"{clean_name}_{timestamp}",
                structure={},
                folder_structure=["src", "docs"],
                meta={"error": str(e), "generated": "fallback"},
                task_file="tasks.md"
            )
    
    async def run_chat(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a chat session with the project agent.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the chat results
        """
        # First generate a project manifest
        manifest = await self.generate_project_manifest(query, teams)
        
        # Get the agents
        executer = self.get_agent("executer")
        planner = self.get_agent("planner")
        
        # Create project directory based on manifest
        project_dir = os.path.join(self.workspace_dir, manifest.directory_name)
        os.makedirs(project_dir, exist_ok=True)
        
        # Create folder structure from manifest
        for folder in manifest.folder_structure:
            folder_path = os.path.join(project_dir, folder)
            os.makedirs(folder_path, exist_ok=True)
            
        # Save manifest in project directory
        manifest_path = os.path.join(project_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            manifest_dict = manifest.dict()
            # Convert datetime to string for JSON serialization
            manifest_dict["created_at"] = manifest.created_at.isoformat()
            json.dump(manifest_dict, f, indent=2)
        
        # Format the message to leverage the LLM's capabilities for project structure creation
        message = f"""
I'd like to plan a project based on the following idea:

{query}

Project has been organized with the following manifest:
{json.dumps(manifest.dict(), indent=2)}

IMPORTANT INSTRUCTIONS:
- Please follow the project structure defined in the manifest
- The project directory is: {project_dir}
- Put all source code in the "src" directory: {os.path.join(project_dir, "src")}
- Put all documentation in the "docs" directory: {os.path.join(project_dir, "docs")}
- Put the tasks.md file in the root directory: {project_dir}
- Create a clear, well-organized project structure
        """
        
        # If teams were specified, add them to the message
        if teams:
            message += f"\n\nPlease assign the following teams: {', '.join(teams)}"
        
        try:
            # Start chat with the project agent and get the result directly
            chat_result = executer.initiate_chat(
                recipient=planner,
                message=message,
                max_turns=10,
            )
            
            # Return the chat results
            return {
                "response": chat_result.summary,
                "chat_history": chat_result.chat_history,
                "manifest": manifest.dict(),
                "project_dir": project_dir
            }
            
        except Exception as e:
            logger.error(f"Error in project chat: {str(e)}")
            return {
                "error": str(e),
                "manifest": manifest.dict(),
                "project_dir": project_dir
            }
