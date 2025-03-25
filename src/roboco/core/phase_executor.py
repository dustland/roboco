"""
Phase Executor Module

This module provides functionality to execute tasks within a single phase.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from roboco.core.models.phase import Phase
from roboco.core.models.task import TaskStatus
from roboco.core.task_manager import TaskManager
from roboco.core.team_assigner import TeamAssigner


class PhaseExecutor:
    """Executes all tasks within a single phase."""
    
    def __init__(self, project_dir: str, workspace_dir: str = None):
        """Initialize the phase executor.
        
        Args:
            project_dir: Project directory containing task data
            workspace_dir: Base workspace directory (defaults to project_dir)
        """
        self.project_dir = project_dir
        self.workspace_dir = workspace_dir or project_dir
        self.team_assigner = TeamAssigner(self.workspace_dir)
        logger.debug(f"Initialized PhaseExecutor for project: {project_dir}")
    
    async def execute_phase(self, phase: Phase, task_manager: TaskManager, tasks_path: str) -> Dict[str, Any]:
        """Execute all tasks in a phase.
        
        Args:
            phase: The phase to execute
            task_manager: TaskManager instance for updating tasks
            tasks_path: Path to the tasks.md file
            
        Returns:
            Results of phase execution
        """
        logger.info(f"Executing phase: {phase.name} with {len(phase.tasks)} tasks")
        
        # Get appropriate team for this phase
        team = self.team_assigner.get_team_for_phase(phase)
        
        # Track results
        results = {
            "phase_name": phase.name,
            "tasks": {},
            "status": "success"
        }
        
        # Execute each task in the phase
        for task in phase.tasks:
            # Skip completed tasks
            if task.status == TaskStatus.DONE:
                logger.debug(f"Task '{task.title}' is already completed, skipping")
                results["tasks"][task.title] = {"status": "already_completed"}
                continue
            
            logger.info(f"Executing task: {task.title}")
            
            # Execute the task
            try:
                # Format the task prompt
                task_prompt = f"""
                Execute the following task:
                
                {task.title}
                
                Details: {task.description if task.description else 'No additional details.'}
                
                Use the project files in {self.project_dir} as needed.
                """
                
                # Execute task using the team
                task_result = await team.run_chat(query=task_prompt)
                
                # Update task status based on result
                if "error" not in task_result:
                    task.status = TaskStatus.DONE
                    task.completed_at = datetime.now()
                    results["tasks"][task.title] = {
                        "status": "completed",
                        "response": task_result.get("response", "")
                    }
                    logger.info(f"Task '{task.title}' completed successfully")
                else:
                    results["tasks"][task.title] = {
                        "status": "failed",
                        "error": task_result.get("error", "Unknown error")
                    }
                    results["status"] = "partial_failure"
                    logger.error(f"Task '{task.title}' failed: {task_result.get('error', 'Unknown error')}")
                
                # Update tasks.md file after each task
                task_manager.update_tasks_file(tasks_path, [phase])
                
            except Exception as e:
                results["tasks"][task.title] = {
                    "status": "failed",
                    "error": str(e)
                }
                results["status"] = "partial_failure"
                logger.error(f"Exception executing task '{task.title}': {e}")
        
        logger.info(f"Phase '{phase.name}' execution completed with status: {results['status']}")
        return results 