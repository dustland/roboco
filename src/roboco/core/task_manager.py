"""
Task Manager Module

This module provides functionality for managing tasks, including parsing, 
updating, executing, and tracking task completion.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from roboco.core.project_fs import ProjectFS
from roboco.core.value_objects.task_status import TaskStatus
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
        
        logger.debug(f"Initialized TaskManager for project: {self.fs.project_id}")
    
    def load(self, tasks_path: str) -> List[Dict[str, Any]]:
        """Parse tasks.md into structured Task objects.
        
        Args:
            tasks_path: Path to the tasks.md file
            
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
                    completed_at=datetime.now().isoformat() if is_completed else None,
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
        
        return tasks
    
    def mark_task_completed(self, tasks: List[Task], task_description: str) -> bool:
        """Mark a specific task as completed.
        
        Args:
            tasks: List of tasks
            task_description: Description of the task to mark as completed
            
        Returns:
            True if the task was found and marked, False otherwise
        """
        for task in tasks:
            if task.description == task_description:
                task.status = TaskStatus.DONE
                task.completed_at = datetime.now().isoformat()
                return True
        
        return False
    
    def save_tasks_md(self, tasks_path: str, tasks: List[Dict[str, Any]]) -> None:
        """Save tasks to tasks.md file in a structured format.
        
        Args:
            tasks_path: Path to the tasks.md file
            tasks: List of task dictionaries
        """
        try:
            # Extract project name from path
            project_name = self.fs.project_id
            
            # Start with the project title
            content = f"# {project_name}\n\n"
            
            # Write each high-level task with its details
            for task in tasks:
                # Get task status and description
                status = task.get("status", "TODO")
                checkbox = "[x]" if status.upper() == "DONE" else "[ ]"
                description = task.get("description", "")
                
                # Write the high-level task
                content += f"- {checkbox} {description}\n"
                
                # Write the task details
                details = task.get("details", [])
                for detail in details:
                    content += f"  * {detail}\n"
                
                # Add a blank line between tasks
                content += "\n"
            
            # Save to file
            self.fs.save_sync(tasks_path, content)
            logger.info(f"Saved tasks to {tasks_path}")
            
        except Exception as e:
            logger.error(f"Error saving tasks.md: {str(e)}")
    
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
        
        This handles special cases like Autogen's ChatResult class.
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation that's JSON serializable
        """
        if obj is None:
            return None
            
        # If it's already a dict, just return it
        if isinstance(obj, dict):
            # Process each value in the dict recursively
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
            
        # If it's a list, convert each item
        if isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
            
        # Handle ChatResult from Autogen
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ChatResult':
            result = {
                'summary': getattr(obj, 'summary', ''),
                'cost': getattr(obj, 'cost', 0),
            }
            
            # Handle chat_history
            if hasattr(obj, 'chat_history'):
                if isinstance(obj.chat_history, list):
                    result['chat_history'] = self._convert_to_dict(obj.chat_history)
                else:
                    result['chat_history'] = str(obj.chat_history)
                    
            return result
            
        # For any other object with attributes, convert to dict if possible
        if hasattr(obj, '__dict__'):
            return {k: self._convert_to_dict(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}
            
        # For basic types (str, int, float, bool, etc.)
        # Just return as is, as they're already serializable
        try:
            # Test if it's JSON serializable
            import json
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            # If not serializable, convert to string
            return str(obj)
            
    def _create_task_header(self, task: Task) -> str:
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
            
    def _create_task_completion_header(self, task: Task, status: str) -> str:
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
        task_header = self._create_task_header(task)
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
            
            # Execute task using the team
            task_result = await team.run_chat(query=task_prompt)
            
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
        completion_header = self._create_task_completion_header(task, results["status"])
        logger.info(completion_header)
        
        logger.info(f"Task '{task.description}' execution completed with status: {results['status']}")
        return results
    
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
    
    async def execute_tasks(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute a list of tasks.
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            Results of task execution
        """
        # Create and log batch header
        batch_header = self._create_batch_task_header(len(tasks))
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
        batch_completion_header = self._create_batch_completion_header(
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
            context_parts.append(f"- Project root: {self.fs.project_id}")
            context_parts.append(f"- Source code directory: {self.src_dir}")
            context_parts.append(f"- Documentation directory: {self.docs_dir}")
            
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
