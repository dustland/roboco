"""
Task Executor Module

This module provides functionality to execute individual tasks.
"""

from typing import Dict, Any
from datetime import datetime
from roboco.core.logger import get_logger
logger = get_logger(__name__)

from roboco.core.models.task import Task, TaskStatus
from roboco.core.task_manager import TaskManager
from roboco.core.team_assigner import TeamAssigner
from roboco.core.project_fs import ProjectFS


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

        logger.debug(f"Initialized TaskExecutor for project: {self.fs.project_dir}")
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task.
        
        Args:
            task: The task to execute
            
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
            
            IMPORTANT DIRECTORY STRUCTURE:
            - Project root: {self.fs.project_dir}
            
            Instructions:
            - Always place source code files (js, py, etc.) in the src directory
            - Always place documentation files (md, txt, etc.) in the docs directory
            - Maintain a clean, organized directory structure
            - Do not create files directly in the project root
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