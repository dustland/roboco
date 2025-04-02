"""
Project Team Module

This module defines the ProjectTeam class, which specializes in project creation
and management through a team of agents.
"""

from typing import Dict, Any, List, Optional

from roboco.core.agent import Agent
from roboco.core.agent_factory import AgentFactory
from roboco.core.config import get_workspace
from roboco.core.project_fs import ProjectFS

class PlanningTeam:
    """Team for creating and managing projects."""
    
    def __init__(self, project_id: str):
        """Initialize the project team.
        
        Args:
            project_id: Optional project ID to use consistently
        """
        # Store project_id for later use
        self.project_id = project_id
        
        # Use a consistent termination message
        TERMINATE_MSG = "TERMINATE"
        
        # Get the agent factory instance
        agent_factory = AgentFactory.get_instance()
        
        # Create executor agent from the factory
        executer = agent_factory.create_agent(
            role_key="executor",
            name="Executer",
            terminate_msg=TERMINATE_MSG,
            code_execution_config={"work_dir": get_workspace() / "code", "use_docker": False}
        )
        
        # Create planner agent from the factory
        planner = agent_factory.create_agent(
            role_key="planner",
            name="Planner",
            terminate_msg=TERMINATE_MSG,
            code_execution_config=False
        )
        
        self.agents = {
            "executer": executer,
            "planner": planner
        }
        
        # Register tools with agents
        from roboco.tools.fs import FileSystemTool
        # Use the project_id if available
        fs = ProjectFS(project_id=self.project_id)
        fs_tool = FileSystemTool(fs=fs)

        fs_tool.register_with_agents(planner, executor_agent=executer)
        
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
    
    async def run_chat(self, query: str, teams: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a chat session with the project agent.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            context: Optional context with additional parameters like project_id
            
        Returns:
            Dict containing the chat results and project directory
        """
        # Get the agents
        executer = self.get_agent("executer")
        planner = self.get_agent("planner")
        
        # Create base message for project planning
        message = f"""Creating a project for this idea: {query}"""
        
        # Add context information if provided
        if context and isinstance(context, dict):
            if "project_id" in context:
                message += f"\n\nIMPORTANT: Use the following project ID: {context['project_id']}"
        
        # Start chat with the project agent and get the result directly
        chat_result = executer.initiate_chat(
            recipient=planner,
            message=message,
            max_turns=20,
        )
        
        # Extract project directory from the response
        project_id = extract_project_id(chat_result.chat_history)
        
        # Use the pre-specified project_id from context if provided and not found in response
        if not project_id and context and "project_id" in context:
            project_id = context["project_id"]
        
        # Return the chat results with project directory
        return {
            "response": chat_result.summary,
            "chat_history": chat_result.chat_history,
            "summary": chat_result.summary,
            "project_id": project_id
        }

def extract_project_id(chat_history) -> Optional[str]:
    """
    Extract the project id from the agent's response.
    
    Args:
        chat_history: The chat history from ChatResult, which can be a list of messages or a string
        
    Returns:
        The extracted project id or None if not found
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
    # Look for JSON response containing project_id
    json_match = re.search(r'```json\s*({.*?})\s*```', response, re.DOTALL)
    if json_match:
        try:
            json_data = json.loads(json_match.group(1))
            if 'project_id' in json_data:
                return json_data['project_id']
        except json.JSONDecodeError:
            pass

    # Look for the standardized format: PROJECT_ID: [project_id]
    match = re.search(r'PROJECT_ID:\s*([a-zA-Z0-9_\-]+)', response)
    if match:
        return match.group(1)
    
    # Try to find "project_id" or similar in the result
    match = re.search(r'[\'"]?project_id[\'"]?:\s*[\'"]([a-zA-Z0-9_\-]+)[\'"]', response)
    if match:
        return match.group(1)
        
    # Try to find project_id in json
    match = re.search(r'"project_id":\s*"([a-zA-Z0-9_\-]+)"', response)
    if match:
        return match.group(1)
    
    return None
