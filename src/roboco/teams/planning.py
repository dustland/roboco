"""
Project Team Module

This module defines the ProjectTeam class, which specializes in project creation
and management through a team of agents.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from datetime import datetime

from roboco.core.agent import Agent
from roboco.core.agent_factory import AgentFactory
from roboco.core.config import get_workspace
from roboco.core.fs import ProjectFS
from roboco.core.team import Team

logger = logger.bind(module=__name__)

class PlanningTeam(Team):
    """Team for creating and managing projects."""
    
    def __init__(self, project_id: str, config_path: Optional[str] = None):
        """Initialize the project team.
        
        Args:
            project_id: Project ID to use consistently
            config_path: Optional path to team configuration file
        """
        # Store project_id for later use
        self.project_id = project_id
        
        # Use a consistent termination message
        TERMINATE_MSG = "TERMINATE"
        
        # Get the agent factory instance
        agent_factory = AgentFactory.get_instance()
        
        # Create filesystem
        fs = ProjectFS(project_id=project_id)
        
        # Create agents first before initializing the parent class
        # Create executor agent from the factory
        executer = agent_factory.create_agent(
            role_key="executor",
            name="Executer",
            terminate_msg=TERMINATE_MSG,
            check_terminate_msg=TERMINATE_MSG,  # Ensure it checks for termination
            code_execution_config={"work_dir": get_workspace() / "code", "use_docker": False}
        )
        
        # Create planner agent from the factory
        planner = agent_factory.create_agent(
            role_key="planner",
            name="Planner",
            terminate_msg=TERMINATE_MSG,
            check_terminate_msg=TERMINATE_MSG,  # Ensure it checks for termination
            code_execution_config=False
        )
        
        # Create agents dictionary
        agents = {
            "executer": executer,
            "planner": planner
        }
        
        # Initialize the parent class with our agents
        super().__init__(name="PlanningTeam", agents=agents, config_path=config_path, fs=fs)
        
        # Register tools with agents
        self._register_tools()
        
    def _register_tools(self):
        """Register necessary tools with the agents."""
        try:
            from roboco.tools.fs import FileSystemTool
            
            # Create file system tool
            fs_tool = FileSystemTool(fs=self.fs)
            
            # Register with agents
            executer = self.get_agent("executer")
            planner = self.get_agent("planner")
            fs_tool.register_with_agents(planner, executor_agent=executer)
            
        except ImportError:
            logger.warning("FileSystemTool not available")
        except Exception as e:
            logger.warning(f"Could not initialize FileSystemTool: {str(e)}")
    
    async def run_chat(self, query: str, teams: Optional[List[str]] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a chat session with the project agent.
        
        Args:
            query: The user's query
            teams: Optional list of teams to assign
            context: Optional context with additional parameters like project_id
            
        Returns:
            Dict containing the chat results, project directory, and project instance
        """
        # Get the agents
        executer = self.get_agent("executer")
        planner = self.get_agent("planner")
        
        # Create base message for project planning
        message = f"""Creating a project for this idea: {query}
        
IMPORTANT: Keep your response focused on planning only - do not write extensive code implementations.
"""
        
        # Add context information if provided
        if context and isinstance(context, dict):
            if "project_id" in context:
                message += f"\n\nIMPORTANT: Use the following project ID: {context['project_id']}"
        
        # Start chat with the project agent and get the result directly
        chat_result = executer.initiate_chat(
            recipient=planner,
            message=message,
            max_turns=10,  # Reduced from 20 to prevent excessive turns
            max_consecutive_auto_reply=5  # Add explicit limit on consecutive auto-replies
        )
        
        # Extract project directory from the response
        project_id = extract_project_id(chat_result.chat_history)
        
        # Use the pre-specified project_id from context if provided and not found in response
        if not project_id and context and "project_id" in context:
            project_id = context["project_id"]
        
        # Variable to hold the project instance
        project_instance = None
        
        # If we have a project_id, ensure it's registered in the database and get the instance
        if project_id:
            try:
                # Import modules here to avoid circular imports
                from roboco.db.service import get_project
                from roboco.core.project_manager import ProjectManager
                
                # Check if project exists in database
                db_project = get_project(project_id)
                
                # If project doesn't exist in DB but was created on disk, initialize the DB record
                if not db_project:
                    logger.info(f"Project {project_id} created on disk but not in database, initializing DB record")
                    # Try to load project data from project.json
                    try:
                        from roboco.core.fs import ProjectFS
                        from sqlalchemy.exc import IntegrityError
                        
                        fs = ProjectFS(project_id=project_id)
                        if fs.exists_sync("project.json"):
                            try:
                                project_data = fs.read_json_sync("project.json")
                                try:
                                    # Initialize the project in DB and get the instance
                                    project_instance = ProjectManager.initialize(
                                        name=project_data.get("name", "Untitled Project"),
                                        description=project_data.get("description", ""),
                                        project_id=project_id,
                                        use_files=False  # Skip file creation since they already exist
                                    )
                                    logger.info(f"Initialized project {project_id} in database from existing files")
                                except IntegrityError as e:
                                    # Handle the case where project was created concurrently
                                    logger.warning(f"Project {project_id} already exists in database (race condition): {str(e)}")
                                    # Load the existing project instead
                                    project_instance = ProjectManager.load(project_id)
                                    logger.info(f"Loaded existing project {project_id} from database")
                            except Exception as e:
                                logger.error(f"Error reading project.json for {project_id}: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error syncing project {project_id} to database: {str(e)}")
                else:
                    # Load the project instance
                    project_instance = ProjectManager.load(project_id)
                    logger.info(f"Loaded project {project_id} from database")
                
                # Apply any metadata from the context
                if project_instance and context and "metadata" in context:
                    metadata = context["metadata"]
                    if isinstance(metadata, dict):
                        changes_made = False
                        for key, value in metadata.items():
                            project_instance.update_metadata(key, value)
                            changes_made = True
                        
                        # Save if we made any changes
                        if changes_made:
                            project_instance.save()
                            logger.info(f"Applied metadata to project {project_id}")
                
                # Always add some standard metadata
                project_instance.update_metadata("created_from_query", query)
                project_instance.update_metadata("created_at", datetime.now().isoformat())
                project_instance.save()
                
            except Exception as e:
                logger.error(f"Error checking project {project_id} database status: {str(e)}")
        
        # Return the chat results with project directory and project instance
        return {
            "response": chat_result.summary,
            "chat_history": chat_result.chat_history,
            "summary": chat_result.summary,
            "project_id": project_id,
            "project": project_instance  # Include the project instance
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
