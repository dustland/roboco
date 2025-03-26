"""
Task Executor Module

This module provides functionality to execute individual tasks.
"""

from typing import Dict, Any, List
from datetime import datetime
from roboco.core.logger import get_logger
logger = get_logger(__name__)

from roboco.core.models.task import Task, TaskStatus
from roboco.core.models.phase import Phase
from roboco.core.task_manager import TaskManager
from roboco.core.team_assigner import TeamAssigner
from roboco.core.project_fs import ProjectFS
from roboco.tools.fs import FileSystemTool


class TaskExecutor:
    """Executes individual tasks."""
    
    def __init__(self, fs: ProjectFS, task_manager: TaskManager):
        """Initialize the task executor.
        
        Args:
            fs: ProjectFS instance
            task_manager: TaskManager instance for updating tasks
        """
        self.fs = fs
        self.task_manager = task_manager
        self.src_dir = "src"
        self.docs_dir = "docs"
        
        self.team_assigner = TeamAssigner(self.fs)
        self.file_tool = FileSystemTool(fs)

        logger.debug(f"Initialized TaskExecutor for project: {self.fs.project_dir}")
    
    def _get_minimal_context(self, current_task: Task, phases: List[Phase]) -> str:
        """Get minimal but essential context for task execution.
        
        Args:
            current_task: The current task being executed
            phases: List of all phases
            
        Returns:
            A string containing minimal context
        """
        context_parts = []
        
        # Get current phase
        current_phase = None
        for phase in phases:
            if current_task in phase.tasks:
                current_phase = phase
                break
        
        if not current_phase:
            return "No phase context available"
            
        # Add basic context
        context_parts.append(f"Current Phase: {current_phase.name}")
        context_parts.append(f"Task: {current_task.description}")
        
        # Add project structure
        try:
            context_parts.append("\nProject Structure:")
            context_parts.append(f"- Project root: {self.fs.project_dir}")
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
    
    async def execute_task(self, task: Task, phases: List[Phase]) -> Dict[str, Any]:
        """Execute a single task.
        
        Args:
            task: The task to execute
            phases: List of all phases for context
            
        Returns:
            Results of task execution
        """
        logger.info(f"Executing task: {task.description}")
        
        # Skip completed tasks
        if task.status == TaskStatus.DONE:
            logger.debug(f"Task '{task.description}' is already completed, skipping")
            return {
                "task": task.description,
                "status": "already_completed"
            }
        
        # Get appropriate team for this task
        team = self.team_assigner.get_team_for_task(task)
        
        # Get minimal context
        execution_context = self._get_minimal_context(task, phases)
        
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
            - Always place source code files (js, py, etc.) in the src directory
            - Always place documentation files (md, txt, etc.) in the docs directory
            - Maintain a clean, organized directory structure
            - Do not create files directly in the project root
            - When modifying files, use the filesystem tool's commands instead of trying to edit files directly
            """
            
            # Execute task using the team
            task_result = await team.run_chat(query=task_prompt)
            
            # Update task status based on result
            if "error" not in task_result:
                task.status = TaskStatus.DONE
                task.completed_at = datetime.now()
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
            results.update({
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"Exception executing task '{task.description}': {e}")
        
        logger.info(f"Task '{task.description}' execution completed with status: {results['status']}")
        return results 