"""
Project Team Module

This module defines the ProjectTeam class, which specializes in project creation
and management through a team of agents.
"""

from typing import Dict, Any, List, Optional

from roboco.core.agent import Agent
from roboco.agents.planner import Planner
from roboco.core.config import get_workspace
from roboco.core.project_fs import FileSystem

class PlanningTeam:
    """Team for creating and managing projects."""
    
    def __init__(self):
        """Initialize the project team.
        """
        
        # Initialize the agents
        executer = Agent(
            name="executer",
            system_message="""You are an execution agent that helps prepare projects.
            When creating files, always put source code in the src directory and documentation in the docs directory.
            """,
            human_input_mode="TERMINATE",
            terminate_msg="TERMINATE",
            llm_config=False,
            code_execution_config={"work_dir": get_workspace() / "code", "use_docker": False}
        )
        planner = Planner(
            name="planner",
            terminate_msg="TERMINATE",
        )
        self.agents = {
            "executer": executer,
            "planner": planner
        }
        
        # Register tools with agents
        from roboco.tools.fs import FileSystemTool
        fs_tool = FileSystemTool(fs=FileSystem(base_dir=get_workspace()))

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
    
    async def run_chat(self, query: str, teams: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run a chat session with the project agent.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            
        Returns:
            Dict containing the chat results and project directory
        """
        # Get the agents
        executer = self.get_agent("executer")
        planner = self.get_agent("planner")
        
        # Format the message for project planning
        message = f"""Creating a project for this idea: {query}"""
                
        # Start chat with the project agent and get the result directly
        chat_result = executer.initiate_chat(
            recipient=planner,
            message=message,
            max_turns=10,
        )
        
        # Extract project directory from the response
        project_directory = extract_project_directory(chat_result.chat_history)
        
        # Return the chat results with project directory
        return {
            "response": chat_result.summary,
            "chat_history": chat_result.chat_history,
            "summary": chat_result.summary,
            "project_dir": project_directory
        }

def extract_project_directory(chat_history) -> Optional[str]:
    """
    Extract the project directory from the agent's response.
    
    Args:
        chat_history: The chat history from ChatResult, which can be a list of messages or a string
        
    Returns:
        The extracted project directory or None if not found
    """
    import re
    import json
    
    # If chat_history is a list, extract the text content from each message
    if isinstance(chat_history, list):
        full_text = ""
        for message in chat_history:
            if isinstance(message, dict) and 'content' in message:
                full_text += message['content'] or "" + "\n"
        response = full_text
    else:
        response = str(chat_history)
    
    # First, try to find direct response from execute_project_manifest (most reliable)
    # Look for JSON response containing directory_name or project_dir
    json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
            if 'directory_name' in json_data:
                return json_data['directory_name']
            elif 'project_dir' in json_data:
                # Extract just the directory name from the full path
                import os
                return os.path.basename(json_data['project_dir'])
        except json.JSONDecodeError:
            pass

    # Look for the standardized format: PROJECT_DIRECTORY: [directory_name]
    match = re.search(r'PROJECT_DIRECTORY:\s*([a-zA-Z0-9_\-]+)', response)
    if match:
        return match.group(1)
    
    # Try to find "project_dir" or similar in the result
    match = re.search(r'[\'"]?project_dir[\'"]?:\s*[\'"]([a-zA-Z0-9_\-]+)[\'"]', response)
    if match:
        return match.group(1)
    
    # Try to find the directory in a success message
    match = re.search(r'successfully.*[\'"]([a-zA-Z0-9_\-]+)[\'"]', response, re.IGNORECASE)
    if match:
        return match.group(1)
        
    # Try to find directory_name in json
    match = re.search(r'"directory_name":\s*"([a-zA-Z0-9_\-]+)"', response)
    if match:
        return match.group(1)
    
    # Look for a reference to a created directory
    match = re.search(r'created\s+(?:at|in|directory|folder|project)\s+[\'"]?([a-zA-Z0-9_\-]+)[\'"]?', response, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None
