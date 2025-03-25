"""
Chat Service

This module provides services for managing chat interactions with project agents.
It follows DDD principles by encapsulating chat-related business logic.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import asyncio
import os
from roboco.core.logger import get_logger

logger = get_logger(__name__)

from roboco.core.models.project import Project
from roboco.core.project_fs import ProjectFS, get_project_fs, ProjectNotFoundError
from roboco.core.config import load_config, get_llm_config, get_workspace
from roboco.teams.planning import PlanningTeam
from roboco.teams.versatile import VersatileTeam
from roboco.core.project_executor import ProjectExecutor
from roboco.core.models import Task


class ChatService:
    """
    Service for managing chat interactions with project agents.
    
    This service follows the DDD principles by encapsulating chat-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self):
        """
        Initialize the chat service with its dependencies.
        """
        # Store conversation history - in a real implementation, this would be persisted
        self.conversations = {}
        
        # Load config for LLM settings
        self.config = load_config()
        self.llm_config = get_llm_config(self.config)
        
        # Set workspace directory from configuration
        self.workspace_dir = str(get_workspace(self.config))
    
    async def start_chat(self, chat_request):
        """
        Process a chat request with the project agent.
        
        Args:
            chat_request: The chat request containing query and other parameters
            
        Returns:
            ChatResponse object with response details
        """
        # Import here to avoid circular dependency
        from roboco.api.models.chat import ChatResponse
        
        # Create a new conversation ID if not provided
        conversation_id = chat_request.conversation_id or str(uuid.uuid4())
        
        # Initialize conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "messages": [],
                "created_at": datetime.now().isoformat(),
                "project_id": None
            }
        
        # Add user message to conversation history
        self.conversations[conversation_id]["messages"].append({
            "role": "user",
            "content": chat_request.query,
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            # For new conversations, we'll use VersatileTeam to plan the project
            if len(self.conversations[conversation_id]["messages"]) == 1:
                # This is the first message in the conversation, so generate a project plan
                return await self._plan_and_execute_project(conversation_id, chat_request)
            else:
                # For continuing conversations, we'll use PlanningTeam for chat interaction
                # Create a new project team for this conversation
                planning_team = PlanningTeam(
                    workspace_dir=self.workspace_dir
                )
                
                # Run the chat session
                chat_result = await planning_team.run_chat(
                    query=chat_request.query,
                    teams=chat_request.teams
                )
                
                # Extract the response
                response_message = chat_result["response"]
                
                # Add agent response to conversation history
                self.conversations[conversation_id]["messages"].append({
                    "role": "assistant",
                    "content": response_message,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Return a properly formatted ChatResponse
                return ChatResponse(
                    conversation_id=conversation_id,
                    message=response_message,
                    project_id=self.conversations[conversation_id].get("project_id"),
                    project_details=None,
                    status="completed"
                )
            
        except Exception as e:
            logger.error(f"Error in chat with project agent: {str(e)}")
            error_message = f"An error occurred while processing your request: {str(e)}"
            
            # Add error to conversation history
            self.conversations[conversation_id]["messages"].append({
                "role": "assistant",
                "content": error_message,
                "timestamp": datetime.now().isoformat()
            })
            
            return ChatResponse(
                conversation_id=conversation_id,
                message=error_message,
                project_id=None,
                status="error"
            )
    
    async def _plan_and_execute_project(self, conversation_id: str, chat_request):
        """
        Plan and execute a project using VersatileTeam.
        
        Args:
            conversation_id: ID of the conversation
            chat_request: The chat request
            
        Returns:
            ChatResponse with the execution details
        """
        # Import here to avoid circular dependency
        from roboco.api.models.chat import ChatResponse
        
        # Create a meaningful project name from the query
        project_name = self._generate_project_name(chat_request.query)
        
        # Create a new project team for this conversation
        versatile_team = VersatileTeam(
            workspace_dir=self.workspace_dir
        )
        
        # Create a proper project structure
        project_dir = os.path.join(self.workspace_dir, project_name)
        
        # Create necessary directories
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(project_dir, "docs"), exist_ok=True)
        
        # Store conversation ID in a metadata file
        with open(os.path.join(project_dir, ".metadata"), "w") as f:
            f.write(f"conversation_id: {conversation_id}\n")
            f.write(f"created_at: {datetime.now().isoformat()}\n")
        
        # Step 1: Use VersatileTeam to generate a project plan (tasks.md)
        planning_task = Task(
            description=f"Plan a project to satisfy this request: {chat_request.query}",
            expected_outcome="Generate a comprehensive tasks.md file that breaks down the project into phases and tasks"
        )
        
        # Execute the planning task
        logger.info(f"Generating project plan for: {chat_request.query}")
        planning_result = await versatile_team.execute_task(planning_task)
        
        if planning_result.get("status") != "completed":
            error_msg = f"Failed to generate project plan: {planning_result.get('error', 'Unknown error')}"
            logger.error(error_msg)
            
            # Add error to conversation history
            self.conversations[conversation_id]["messages"].append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            
            return ChatResponse(
                conversation_id=conversation_id,
                message=error_msg,
                project_id=None,
                status="error"
            )
        
        # Check if tasks.md was created
        tasks_file_path = os.path.join(project_dir, "tasks.md")
        if not os.path.exists(tasks_file_path):
            # If not explicitly created, generate it from the planning results
            with open(tasks_file_path, "w") as f:
                f.write("# Project Tasks\n\n")
                
                # Extract task information from the planning result
                if "summary" in planning_result:
                    f.write(f"## Plan\n{planning_result['summary']}\n\n")
                
                # Create a default phase with tasks based on the planning result
                f.write("## Implementation\n\n")
                f.write("- [ ] Implement the solution based on the plan\n")
                f.write("- [ ] Test the implementation\n")
                f.write("- [ ] Document the solution\n")
        
        # Step 2: Register the project
        project = Project(
            name=project_name,
            description=chat_request.query,
            directory=project_dir,
            teams=chat_request.teams or ["versatile"]
        )
        
        # Save the project
        project_fs = ProjectFS.create(project)
        project_id = project.id
        
        # Update conversation with project ID
        self.conversations[conversation_id]["project_id"] = project_id
        
        # Step 3: Execute the project
        executor = ProjectExecutor(project_dir)
        execution_result = await executor.execute_project()
        
        # Prepare response message
        if execution_result.get("error"):
            response_message = f"I've planned your project but encountered an error during execution: {execution_result.get('error')}"
            status = "partial_success"
        else:
            response_message = f"I've successfully executed your request: {chat_request.query}\n\n"
            
            # Add phase results to the response
            if "phases" in execution_result:
                for phase_name, phase_result in execution_result["phases"].items():
                    response_message += f"\n## {phase_name}\n"
                    for task_name, task_result in phase_result.get("tasks", {}).items():
                        task_status = task_result.get("status", "unknown")
                        if task_status == "completed":
                            response_message += f"- ✅ {task_name}\n"
                        else:
                            response_message += f"- ❌ {task_name}: {task_result.get('error', 'Failed')}\n"
            
            response_message += f"\nYou can find all project files in: {project_dir}"
            status = "completed"
        
        # Add response to conversation history
        self.conversations[conversation_id]["messages"].append({
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Prepare project details
        project_details = {
            "name": project.name,
            "description": project.description,
            "directory": project.directory,
            "teams": project.teams
        }
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=response_message,
            project_id=project_id,
            project_details=project_details,
            status=status
        )
    
    def _generate_project_name(self, query: str) -> str:
        """
        Generate a meaningful project name from the query.
        
        Args:
            query: The user's query
            
        Returns:
            A meaningful project name
        """
        # Clean and normalize the query to create a meaningful folder name
        words = query.lower().split()[:5]  # Use first 5 words
        name = "_".join(words)
        name = "".join(c if c.isalnum() or c == "_" else "_" for c in name)
        
        # Ensure the name is not too long
        if len(name) > 50:
            name = name[:50]
        
        # Add a timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"{name}_{timestamp}"
    
    async def get_conversation_history(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the history of a conversation.
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            Dictionary with conversation details if found, None otherwise
        """
        return self.conversations.get(conversation_id)
        
    async def _get_project_executor(self, project_dir: str):
        """
        Get a ProjectExecutor instance for the given project directory.
        
        Args:
            project_dir: Directory of the project
            
        Returns:
            A ProjectExecutor instance
        """
        from roboco.core.project_executor import ProjectExecutor
        return ProjectExecutor(project_dir)
