"""
Task Manager Module

This module provides functionality for managing tasks, including parsing, 
updating, executing, and tracking task completion.
"""
import re
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any
import markdown
from bs4 import BeautifulSoup
import os

from roboco.core.fs import ProjectFS
from roboco.core.models.task import TaskStatus
from roboco.core.models import Task
from roboco.core.team_manager import TeamManager
from loguru import logger

from roboco.utils.id_generator import generate_short_id

logger = logger.bind(module=__name__)


class TaskManager:
    """Component for parsing, updating, executing, and managing tasks."""
    
    def __init__(self, fs: ProjectFS):
        """Initialize the task manager.
        
        Args:
            fs: ProjectFS instance for file operations
        """
        self.fs = fs
        
        # Initialize team manager for task execution
        self.team_manager = TeamManager(fs=fs)
        
        # Import FileSystemTool here to avoid circular imports
        from roboco.tools.fs import FileSystemTool
        self.file_tool = FileSystemTool(fs)
        
        # Log initialization without accessing potentially missing attributes
        logger.debug(f"Initialized TaskManager")
    
    def parse_tasks_from_markdown(self, markdown_content: str, project_id: str) -> List[Task]:
        """
        Parse tasks from markdown format into Task objects.
        
        Uses the markdown package to convert markdown to HTML, then
        BeautifulSoup to parse the HTML structure for tasks.
        
        Args:
            markdown_content: Markdown content containing task definitions
            project_id: ID of the project the tasks belong to
            
        Returns:
            List of Task objects
        """
        tasks = []
        
        # Convert markdown to HTML and parse with BeautifulSoup
        html = markdown.markdown(markdown_content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all h2 headers (## Task: Title)
        h2_elements = soup.find_all('h2')
        
        for h2 in h2_elements:
            # Handle both old format (status in heading) and new format (status after heading)
            title_text = ""
            status = TaskStatus.TODO  # Default status
            
            # Check if we have the old format with status in heading
            if '[x]' in h2.text or '[ ]' in h2.text:
                # Old format: extract status from heading
                status = TaskStatus.COMPLETED if '[x]' in h2.text else TaskStatus.TODO
                # Clean up the title text
                title_text = h2.text.replace('[x]', '').replace('[ ]', '').replace('Task:', '').strip()
            elif 'Task:' in h2.text:
                # New format: extract title only from heading
                title_text = h2.text.replace('Task:', '').strip()
            else:
                # Not a task heading, skip it
                continue
                
            # Find next sibling elements to find status indicator, description and details
            current = h2.next_sibling
            description = title_text  # Default to title if no description found
            details = []
            desc_found = False
            status_found = False
            
            # Process elements after the heading
            while current and not (current.name == 'h2'):
                # Check if this is the status indicator line (only for new format)
                if not status_found and current.name and current.text and ('[x]' in current.text or '[ ]' in current.text):
                    status = TaskStatus.COMPLETED if '[x]' in current.text else TaskStatus.TODO
                    status_found = True
                # Otherwise, if it's a paragraph and we haven't found description yet, treat as description
                elif current.name == 'p' and not desc_found:
                    # Skip the status indicator paragraph
                    if not ('[x]' in current.text or '[ ]' in current.text):
                        description = current.text.strip()
                        desc_found = True
                # If it's a list, extract detail points
                elif current.name == 'ul':
                    for li in current.find_all('li'):
                        details.append(li.text.strip())
                current = current.next_sibling
            
            # Create task metadata
            meta = {"details": details} if details else {}
            
            # Create the Task object
            task = Task(
                id=generate_short_id(),
                title=title_text,
                description=description,
                status=status,
                project_id=project_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                meta=meta
            )
            
            tasks.append(task)
        
        logger.info(f"Parsed {len(tasks)} tasks from markdown using HTML parsing")
        return tasks
    
    def tasks_to_markdown(self, tasks: List[Task], project_name: str) -> str:
        """
        Convert Task objects to markdown format.
        
        Args:
            tasks: List of Task objects
            project_name: Name of the project for the markdown header
            
        Returns:
            Markdown string representation of the tasks
        """
        lines = [f"# Tasks for {project_name}", ""]
        
        for task in tasks:
            # Add the heading first, then the checkbox as a separate element
            lines.append(f"## Task: {task.title}")
            
            # Add status indicator on the next line, not inside the heading
            status_indicator = "x" if task.status == TaskStatus.COMPLETED else " "
            lines.append(f"- [{status_indicator}] Status: {'Completed' if task.status == TaskStatus.COMPLETED else 'Todo'}")
            lines.append("")
            
            # Add description
            lines.append(f"{task.description}")
            lines.append("")
            
            # Add details
            details = task.meta.get("details", []) if task.meta else []
            if details:
                for detail in details:
                    lines.append(f"- {detail}")
                lines.append("")
        
        return "\n".join(lines)
    
    def load_tasks(self, project_id: str) -> List[Task]:
        """
        Load tasks from the database for a project.
        
        Args:
            project_id: ID of the project to load tasks for
            
        Returns:
            List of Task objects
        """
        from roboco.db.service import get_tasks_by_project
        return get_tasks_by_project(project_id)
    
    def generate_task_context(self, current_task: Task, tasks: List[Task], project_info: Dict[str, Any]) -> str:
        """
        Generate context information about a task and its project.
        
        Args:
            current_task: The current task being executed
            tasks: List of all tasks in the project
            project_info: Dictionary with project information
            
        Returns:
            String containing formatted context information
        """
        context_parts = []
        
        # Project information
        context_parts.append(f"# Project Context\n")
        context_parts.append(f"- Project name: {project_info.get('name', 'Unknown')}")
        context_parts.append(f"- Description: {project_info.get('description', 'No description')}")
        context_parts.append(f"- Project root: {project_info.get('id', 'Unknown')}")
        
        # Add other tasks for context
        task_summaries = []
        for task in tasks:
            if task.description != current_task.description:
                status = "COMPLETED" if task.status == TaskStatus.COMPLETED else "TODO"
                task_summaries.append(f"- {task.description} [{status}]")
        
        if task_summaries:
            context_parts.append("\nOther tasks in project:")
            context_parts.extend(task_summaries)
        
        # Add project structure if we have that info
        src_dir = project_info.get('source_code_dir', 'src')
        docs_dir = project_info.get('docs_dir', 'docs')
        
        try:
            context_parts.append("\nProject Structure:")
            context_parts.append(f"- Project root: {project_info.get('id', 'Unknown')}")
            context_parts.append(f"- Source code directory: {src_dir}")
            context_parts.append(f"- Documentation directory: {docs_dir}")
            
            # List top-level directories and files if we have access
            if hasattr(self.fs, 'list_sync'):
                root_items = self.fs.list_sync(".")
                if root_items:
                    context_parts.append("\nRoot Directory Contents:")
                    for item in root_items:
                        if item not in [src_dir, docs_dir]:
                            context_parts.append(f"- {item}")
        except Exception as e:
            logger.warning(f"Could not get project structure: {e}")
        
        return "\n".join(context_parts)
    
    def create_header(self, text: str, style: str = "task", status: Optional[str] = None) -> str:
        """
        Create a visually distinct header with consistent styling.
        
        Args:
            text: The text to display in the header
            style: The header style ("task", "complete", or "batch")
            status: Optional status indicator for completion headers
            
        Returns:
            A formatted header string
        """
        if style == "task":
            separator = "=" * 80
            heading = f" EXECUTING TASK: {text} "
            symbol = ""
        elif style == "complete":
            separator = "-" * 80
            status_symbol = "✅" if status == "completed" else "❌" if status == "failed" else "⏩"
            heading = f" {status_symbol} TASK COMPLETE: {text} [{status.upper()}] "
            symbol = status_symbol
        elif style == "batch":
            separator = "*" * 80
            heading = f" BEGINNING EXECUTION OF {text} TASKS "
            symbol = ""
        elif style == "batch_complete":
            separator = "*" * 80
            status_info = text.split("/")
            completed, total = int(status_info[0]), int(status_info[1])
            status_symbol = "✅" if status == "success" else "⚠️" if status == "partial_failure" else "❌"
            heading = f" {status_symbol} TASK BATCH COMPLETE: {completed}/{total} tasks completed successfully [{status.upper()}] "
            symbol = status_symbol
        else:
            separator = "-" * 80
            heading = f" {text} "
            symbol = ""
            
        # Center the heading within the separator
        centered_heading = heading.center(80, separator[0])
        
        return f"\n{separator}\n{centered_heading}\n{separator}\n"
    
    # Use the unified create_header method instead of these specialized methods
    create_task_header = lambda self, task: self.create_header(task.description, "task")
    create_task_completion_header = lambda self, task, status: self.create_header(task.description, "complete", status)
    create_batch_task_header = lambda self, num_tasks: self.create_header(str(num_tasks), "batch")
    create_batch_completion_header = lambda self, status, completed, total: self.create_header(f"{completed}/{total}", "batch_complete", status)
    
    def _convert_to_dict(self, obj):
        """
        Convert a potentially non-serializable object to a dictionary.
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation that's JSON serializable
        """
        if obj is None:
            return None
            
        # If it's already a dict, just process each value recursively
        if isinstance(obj, dict):
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
            
        # If it's a list, convert each item
        if isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
            
        # For objects with a to_dict method, use that
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return self._convert_to_dict(obj.to_dict())
            
        # For objects with __dict__, convert to dictionary
        if hasattr(obj, '__dict__'):
            return {k: self._convert_to_dict(v) for k, v in obj.__dict__.items() 
                   if not k.startswith('_')}
            
        # Try to serialize, otherwise convert to string
        try:
            import json
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)
            
    async def execute_task(self, task: Task, tasks: List[Task] = None) -> Dict[str, Any]:
        """Execute a single task.
        
        Args:
            task: Task to execute
            tasks: Optional list of all tasks for context
            
        Returns:
            Results of task execution
        """
        # Skip already completed tasks
        if task.status == TaskStatus.COMPLETED:
            logger.info(f"Task '{task.description}' is already marked as completed, skipping execution")
            return {
                "task": task.description,
                "status": "already_completed"
            }
        
        # Create and log an outstanding header for this task
        task_header = self.create_task_header(task)
        logger.info(task_header)
        logger.info(f"Executing task: {task.description}")
        
        # Get appropriate team for this task
        team = self.team_manager.get_team_for_task(task)
        
        # Get minimal context
        execution_context = self._get_minimal_context(task, tasks)
        
        # Track results
        results = {
            "task": task.description,
            "status": "success"
        }
        
        try:
            # Format the task prompt
            task_prompt = f"""
Execute the following task:

{task.description}

CONTEXT:
{execution_context}

Instructions:
- You have access to the filesystem tool for all file operations
- Use the filesystem tool's commands to:
    * `list_directory` to explore directories and see what files exist
    * `read_file` to read file contents
    * `save_file` to create or modify files
    * `file_exists` to check if a file exists
    * `create_directory` to create new directories
    * `delete_file` to remove files
    * `read_json` to read and parse JSON files
- Maintain a clean, organized directory structure
- Use the filesystem tool's commands instead of trying to edit files directly
"""
            
            # Set up message recording
            original_send_fn = team.send_message
            messages = []
            
            # Wrap the send_message function to record messages
            async def record_message_wrapper(agent_id, content, role="assistant", **kwargs):
                # Record the message
                message = {
                    "agent_id": agent_id,
                    "content": content,
                    "role": role,
                    "timestamp": datetime.now().isoformat(),
                    **kwargs
                }
                messages.append(message)
                
                # Call the original function
                return await original_send_fn(agent_id, content, role, **kwargs)
                
            # Replace the send_message function with our wrapper
            team.send_message = record_message_wrapper
            
            # Execute task using the team
            task_result = await team.run_chat(query=task_prompt)
            
            # Store recorded messages
            results["messages"] = messages
            
            # Restore original send_message function
            team.send_message = original_send_fn
            
            # Convert any non-serializable objects to dictionaries
            task_result = self._convert_to_dict(task_result)
            
            # Update task status based on result
            if "error" not in task_result:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now().isoformat()
                results.update({
                    "status": "completed",
                    "response": task_result.get("response", "")
                })
                logger.info(f"Task '{task.description}' completed successfully")
            else:
                results.update({
                    "status": "failed",
                    "error": task_result.get("error", "Unknown error")
                })
                logger.error(f"Task '{task.description}' failed: {task_result.get('error', 'Unknown error')}")
            
            # Save the recorded messages to the database
            await self._save_task_messages(task.id, messages)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            results.update({
                "status": "failed",
                "error": str(e),
                "error_details": error_details
            })
            logger.error(f"Exception executing task '{task.description}': {e}")
            logger.error(f"Traceback: {error_details}")
        
        # Add completion header
        completion_header = self.create_task_completion_header(task, results["status"])
        logger.info(completion_header)
        
        logger.info(f"Task '{task.description}' execution completed with status: {results['status']}")
        return results
    
    async def _save_task_messages(self, task_id: str, messages: List[Dict[str, Any]]) -> None:
        """
        Save messages generated during task execution to the database.
        
        Args:
            task_id: ID of the task
            messages: List of message dictionaries with agent_id, content, role, etc.
        """
        try:
            from roboco.db.service import create_message
            from roboco.core.models.message import Message, MessageRole, MessageType
            
            # Import these for db session
            from roboco.db import get_session
            
            for msg in messages:
                # Create a Message object directly
                message = Message(
                    content=msg.get("content", ""),
                    role=msg.get("role", "assistant"),
                    type=msg.get("type", MessageType.TEXT),
                    task_id=task_id,  # Set the task ID directly
                    agent_id=msg.get("agent_id"),
                    meta=msg.get("meta", {})
                )
                
                # Create the message in the database
                create_message(task_id, message)
                    
            logger.info(f"Saved {len(messages)} messages for task {task_id}")
        except Exception as e:
            logger.error(f"Error saving messages for task {task_id}: {str(e)}")
            logger.error(traceback.format_exc())
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute a list of tasks.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Results of task execution
        """
        # Create and log batch header
        batch_header = self.create_batch_task_header(len(tasks))
        logger.info(batch_header)
        logger.info(f"Executing {len(tasks)} tasks")
        
        # Track results
        results = {
            "tasks": {},
            "status": "success"
        }
        
        # Track completion stats
        completed_count = 0
        
        # Execute each task
        for task in tasks:
            task_result = await self.execute_task(task, tasks)
            
            # Convert result to ensure it's serializable
            task_result = self._convert_to_dict(task_result)
            
            results["tasks"][task.description] = task_result
            
            # Update completion stats
            if task_result["status"] == "completed" or task_result["status"] == "already_completed":
                completed_count += 1
            
            # Update overall status if any task failed
            if task_result["status"] != "completed" and task_result["status"] != "already_completed":
                results["status"] = "partial_failure"
        
        # Create and log batch completion header
        batch_completion_header = self.create_batch_completion_header(
            results["status"], 
            completed_count, 
            len(tasks)
        )
        logger.info(batch_completion_header)
        
        logger.info(f"Tasks execution completed with status: {results['status']}")
        return results
    
    def _get_minimal_context(self, current_task: Task, tasks: List[Task] = None) -> str:
        """Get minimal but essential context for task execution.
        
        Args:
            current_task: The current task being executed
            tasks: Optional list of all tasks for context
            
        Returns:
            A string containing minimal context
        """
        context_parts = []
        
        # Add current task information with clear heading
        context_parts.append("## Current Task")
        context_parts.append(f"Title: {current_task.title}")
        context_parts.append(f"Description: {current_task.description}")
        context_parts.append(f"Status: {current_task.status.value}")
        
        # Add other tasks if available with clear separation
        if tasks:
            task_summaries = []
            for task in tasks:
                if task.id != current_task.id:  # Use ID comparison for safety
                    status = "COMPLETED" if task.status == TaskStatus.COMPLETED else "TODO"
                    task_summaries.append(f"- Title: {task.title}")
                    task_summaries.append(f"  Description: {task.description}")
                    task_summaries.append(f"  Status: {status}")
            
            if task_summaries:
                context_parts.append("\n## Other Tasks")
                context_parts.extend(task_summaries)
        
        # Add project structure information with clear heading
        try:
            # Get project ID from base directory name
            project_id = os.path.basename(self.fs.base_dir)
            
            # Add basic project structure information
            context_parts.append("\n## Project Structure")
            context_parts.append(f"- Project root: {project_id}")
            context_parts.append(f"- Source code directory: src")
            context_parts.append(f"- Documentation directory: docs")
            
            # List top-level directories and files with clear heading
            root_items = self.fs.list_sync(".")
            if root_items:
                context_parts.append("\n## Root Directory Contents")
                for item in root_items:
                    context_parts.append(f"- {item}")
        
        except Exception as e:
            logger.warning(f"Could not get project structure: {e}")
        
        return "\n".join(context_parts)
