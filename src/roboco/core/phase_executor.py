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
        self.src_dir = os.path.join(self.project_dir, "src")
        self.docs_dir = os.path.join(self.project_dir, "docs")
        
        # Create directories if they don't exist
        os.makedirs(self.src_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)
        
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
            "status": "success",
            "directory_structure": {
                "project": self.project_dir,
                "src": self.src_dir,
                "docs": self.docs_dir
            }
        }
        
        # Execute each task in the phase
        for task in phase.tasks:
            # Skip completed tasks
            if task.status == TaskStatus.DONE:
                logger.debug(f"Task '{task.description}' is already completed, skipping")
                results["tasks"][task.description] = {"status": "already_completed"}
                continue
            
            logger.info(f"Executing task: {task.description}")
            
            # Execute the task
            try:
                # Format the task prompt
                task_prompt = f"""
                Execute the following task:
                
                {task.description}
                
                IMPORTANT DIRECTORY STRUCTURE:
                - Project root: {self.project_dir}
                - Source code directory: {self.src_dir} (Put all code here)
                - Documentation directory: {self.docs_dir} (Put all documentation here)
                
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
                    results["tasks"][task.description] = {
                        "status": "completed",
                        "response": task_result.get("response", "")
                    }
                    logger.info(f"Task '{task.description}' completed successfully")
                else:
                    results["tasks"][task.description] = {
                        "status": "failed",
                        "error": task_result.get("error", "Unknown error")
                    }
                    results["status"] = "partial_failure"
                    logger.error(f"Task '{task.description}' failed: {task_result.get('error', 'Unknown error')}")
                
                # Update tasks.md file after each task
                task_manager.update_tasks_file(tasks_path, [phase])
                
            except Exception as e:
                results["tasks"][task.description] = {
                    "status": "failed",
                    "error": str(e)
                }
                results["status"] = "partial_failure"
                logger.error(f"Exception executing task '{task.description}': {e}")
        
        logger.info(f"Phase '{phase.name}' execution completed with status: {results['status']}")
        return results 