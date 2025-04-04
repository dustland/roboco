"""
Task Manager Module

This module provides functionality for managing tasks, including parsing, 
updating, executing, and tracking task completion.
"""
import logging
import re
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any

from roboco.core.fs import ProjectFS
from roboco.core.models.task import TaskStatus
from roboco.core.models import Task
from roboco.core.team_manager import TeamManager
from loguru import logger

logger = logger.bind(module=__name__)


class TaskManager:
    """Component for parsing, updating, executing, and managing tasks."""
    
    def __init__(self, fs: ProjectFS):
        """Initialize the task manager.
        
        Args:
            fs: ProjectFS instance for file operations
        """
        self.fs = fs
        self.src_dir = "src"
        self.docs_dir = "docs"
        
        # Initialize team manager for task execution
        self.team_manager = TeamManager(fs=fs)
        
        # Import FileSystemTool here to avoid circular imports
        from roboco.tools.fs import FileSystemTool
        self.file_tool = FileSystemTool(fs)
        
        # Log initialization without accessing potentially missing attributes
        logger.debug(f"Initialized TaskManager")
    
    def load_tasks(self, tasks_path: str = "tasks.md") -> List[Task]:
        """
        Load tasks from tasks.md into Task objects.
        
        Args:
            tasks_path: Path to the tasks file, defaults to "tasks.md"
            
        Returns:
            List of Task objects
        """
        tasks = []
        current_task = None
        task_details = []
        
        try:
            content = self.fs.read_sync(tasks_path)
            lines = content.split('\n')
        except FileNotFoundError:
            logger.error(f"Tasks file not found: {tasks_path}")
            return tasks
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Skip the project title (first line)
            if line.startswith('# ') and not tasks:
                continue
            
            # Parse task items (high-level tasks)
            if line.startswith('- [ ]') or line.startswith('- [x]'):
                # If we were processing a task, save it with its details
                if current_task is not None:
                    current_task.details = task_details
                    tasks.append(current_task)
                    task_details = []
                
                is_completed = line.startswith('- [x]')
                task_description = line[5:].strip()
                
                # Create Task
                current_task = Task(
                    description=task_description,
                    status=TaskStatus.DONE if is_completed else TaskStatus.TODO,
                    completed_at=datetime.now() if is_completed else None,
                    details=[]
                )
            
            # Parse task details (bullet points)
            elif line.startswith('  * ') and current_task is not None:
                detail = line[4:].strip()  # Extract the detail text
                task_details.append(detail)
        
        # Add the last task if there is one
        if current_task is not None:
            current_task.details = task_details
            tasks.append(current_task)
        
        logger.debug(f"Loaded {len(tasks)} tasks from {tasks_path}")
        return tasks
    
    def mark_task_completed(self, task: Task, tasks_path: str = "tasks.md") -> bool:
        """
        Mark a specific task as completed in the tasks file.
        This method updates only the checkbox status in the tasks.md file without
        overwriting the entire file content.
        
        Args:
            task: The task to mark as completed
            tasks_path: Path to the tasks file, defaults to "tasks.md"
            
        Returns:
            True if the task was successfully marked, False otherwise
        """
        try:
            # Try to read the existing file
            content = self.fs.read_sync(tasks_path)
            
            # Use regex to update task status while preserving all other content
            updated_lines = []
            task_found = False
            
            for line in content.split('\n'):
                # Check if this line has a task marker
                task_match = re.match(r'^- \[([ x])\] (.+)$', line)
                if task_match:
                    status_char = task_match.group(1)
                    task_desc = task_match.group(2)
                    
                    # If this task matches our target, update its status
                    if task_desc == task.description:
                        task_found = True
                        if status_char != 'x':  # Only update if not already completed
                            logger.info(f"Updating task status: '{task_desc}' -> DONE")
                            line = f"- [x] {task_desc}"
                
                updated_lines.append(line)
            
            # If task wasn't found, no updates needed
            if not task_found:
                logger.warning(f"Task '{task.description}' not found in {tasks_path}")
                return False
            
            # Write the updated content back to the file
            updated_content = '\n'.join(updated_lines)
            self.fs.write_sync(tasks_path, updated_content)
            logger.info(f"Updated task status for '{task.description}' in {tasks_path}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Tasks file not found: {tasks_path}")
            return False
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    def create_initial_tasks_file(self, tasks: List[Task], tasks_path: str = "tasks.md") -> bool:
        """
        Create initial tasks.md file with proper formatting.
        Only use this if the file doesn't exist yet.
        
        Args:
            tasks: List of tasks to include
            tasks_path: Path to the tasks file, defaults to "tasks.md"
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Start with the project title
            content = f"# Project Tasks\n\n"
            
            # Write each task with its proper format
            for task in tasks:
                status_char = 'x' if task.status == TaskStatus.DONE else ' '
                content += f"- [{status_char}] {task.description}\n"
                
                # Add task details as bullet points
                if task.details:
                    for detail in task.details:
                        content += f"  * {detail}\n"
                content += "\n"
                
            # Write to file
            self.fs.write_sync(tasks_path, content)
            logger.info(f"Created new tasks file at {tasks_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tasks file: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
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
        # Create list of context information
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
                status = "DONE" if task.status == TaskStatus.DONE else "TODO"
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
    
    def create_task_header(self, task: Task) -> str:
        """
        Create a visually distinct header for task execution.
        
        Args:
            task: The task being executed
            
        Returns:
            A formatted header string
        """
        separator = "=" * 80
        task_title = f" EXECUTING TASK: {task.description} "
        
        # Center the task title within the separator
        centered_title = task_title.center(80, "=")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
            
    def create_task_completion_header(self, task: Task, status: str) -> str:
        """
        Create a visually distinct header for task completion.
        
        Args:
            task: The task that was executed
            status: The completion status
            
        Returns:
            A formatted completion header string
        """
        separator = "-" * 80
        status_symbol = "✅" if status == "completed" else "❌" if status == "failed" else "⏩"
        task_title = f" {status_symbol} TASK COMPLETE: {task.description} [{status.upper()}] "
        
        # Center the task title within the separator
        centered_title = task_title.center(80, "-")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
    
    def load(self, tasks_path: str) -> List[Dict[str, Any]]:
        """
        Legacy method. Use load_tasks() instead.
        
        Args:
            tasks_path: Path to the tasks.md file
            
        Returns:
            List of Task objects
        """
        logger.warning("Using deprecated load() method, consider switching to load_tasks()")
        return self.load_tasks(tasks_path)
    
    def get_task_by_description(self, tasks: List[Task], task_description: str) -> Optional[Task]:
        """Get a task by description.
        
        Args:
            tasks: List of tasks to search
            task_description: Description of the task to find
            
        Returns:
            Task if found, None otherwise
        """
        for task in tasks:
            if task.description.lower() == task_description.lower():
                return task
        return None
    
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
        if task.status == TaskStatus.DONE:
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

Details:
{chr(10).join([f"* {detail}" for detail in task.details]) if task.details else "No additional details provided."}

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
- Always place source code files (js, py, etc.) in the src directory
- Always place documentation files (md, txt, etc.) in the docs directory
- Maintain a clean, organized directory structure
- Do not create files directly in the project root
- When modifying files, use the filesystem tool's commands instead of trying to edit files directly
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
                task.status = TaskStatus.DONE
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
            from roboco.core.models.message import MessageCreate, MessageRole, MessageType
            
            # Import these for db session
            from roboco.db import get_session
            
            for msg in messages:
                # Convert the message to a MessageCreate object
                message_data = MessageCreate(
                    content=msg.get("content", ""),
                    role=msg.get("role", "assistant"),
                    type=msg.get("type", MessageType.TEXT),
                    agent_id=msg.get("agent_id"),
                    meta=msg.get("meta", {})
                )
                
                # Create the message in the database with explicit task_id
                create_message(task_id, message_data)
                    
            logger.info(f"Saved {len(messages)} messages for task {task_id}")
        except Exception as e:
            logger.error(f"Error saving messages for task {task_id}: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _create_batch_task_header(self, num_tasks: int) -> str:
        """
        Create a visually distinct header for a batch of tasks.
        
        Args:
            num_tasks: Number of tasks to be executed
            
        Returns:
            A formatted header string
        """
        separator = "*" * 80
        title = f" BEGINNING EXECUTION OF {num_tasks} TASKS "
        
        # Center the title within the separator
        centered_title = title.center(80, "*")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
        
    def _create_batch_completion_header(self, status: str, completed: int, total: int) -> str:
        """
        Create a visually distinct header for batch task completion.
        
        Args:
            status: Overall status of the batch
            completed: Number of successfully completed tasks
            total: Total number of tasks
            
        Returns:
            A formatted completion header string
        """
        separator = "*" * 80
        status_symbol = "✅" if status == "success" else "⚠️" if status == "partial_failure" else "❌"
        title = f" {status_symbol} TASK BATCH COMPLETE: {completed}/{total} tasks completed successfully [{status.upper()}] "
        
        # Center the title within the separator
        centered_title = title.center(80, "*")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
    
    def create_batch_task_header(self, num_tasks: int) -> str:
        """
        Create a visually distinct header for a batch of tasks.
        
        Args:
            num_tasks: Number of tasks to be executed
            
        Returns:
            A formatted header string
        """
        separator = "*" * 80
        title = f" BEGINNING EXECUTION OF {num_tasks} TASKS "
        
        # Center the title within the separator
        centered_title = title.center(80, "*")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
        
    def create_batch_completion_header(self, status: str, completed: int, total: int) -> str:
        """
        Create a visually distinct header for batch task completion.
        
        Args:
            status: Overall status of the batch
            completed: Number of successfully completed tasks
            total: Total number of tasks
            
        Returns:
            A formatted completion header string
        """
        separator = "*" * 80
        status_symbol = "✅" if status == "success" else "⚠️" if status == "partial_failure" else "❌"
        title = f" {status_symbol} TASK BATCH COMPLETE: {completed}/{total} tasks completed successfully [{status.upper()}] "
        
        # Center the title within the separator
        centered_title = title.center(80, "*")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
    
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
        
        # Add basic context
        context_parts.append(f"Task: {current_task.description}")
        
        # Add other tasks if available for context
        if tasks:
            task_summaries = []
            for task in tasks:
                if task != current_task:
                    status = "DONE" if task.status == TaskStatus.DONE else "TODO"
                    task_summaries.append(f"- {task.description} [{status}]")
            
            if task_summaries:
                context_parts.append("\nOther tasks in project:")
                context_parts.extend(task_summaries)
        
        # Add project structure
        try:
            context_parts.append("\nProject Structure:")
            context_parts.append("- Source code directory: src")
            context_parts.append("- Documentation directory: docs")
            
            # List top-level directories and files
            root_items = self.fs.list_sync(".")
            if root_items:
                context_parts.append("\nRoot Directory Contents:")
                for item in root_items:
                    if item not in [self.src_dir, self.docs_dir]:
                        context_parts.append(f"- {item}")
        
        except Exception as e:
            logger.warning(f"Could not get project structure: {e}")
        
        return "\n".join(context_parts)
