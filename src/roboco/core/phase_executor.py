"""
Phase Executor Module

This module provides functionality to execute tasks within a single phase.
"""

from typing import Dict, Any
from datetime import datetime
from roboco.core.logger import get_logger
logger = get_logger(__name__)

from roboco.core.models.phase import Phase
from roboco.core.models.task import TaskStatus
from roboco.core.task_manager import TaskManager
from roboco.core.team_assigner import TeamAssigner
from roboco.core.project_fs import ProjectFS


class PhaseExecutor:
    """Executes all tasks within a single phase."""
    
    def __init__(self, fs: ProjectFS, task_manager: TaskManager):
        """Initialize the phase executor.
        
        Args:
            fs: ProjectFS instance
        """
        self.fs = fs
        self.task_manager = task_manager
        self.src_dir = "src"
        self.docs_dir = "docs"
        
        self.team_assigner = TeamAssigner(self.fs)

        logger.debug(f"Initialized PhaseExecutor for project: {self.fs.project_dir}")
    
    async def execute_phase(self, phase: Phase) -> Dict[str, Any]:
        """Execute all tasks in a phase.
        
        Args:
            phase: The phase to execute
            task_manager: TaskManager instance for updating tasks
            
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
                "project": self.fs.project_dir,
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
                self.task_manager.mark_task_completed(phase, task.description)
                
            except Exception as e:
                results["tasks"][task.description] = {
                    "status": "failed",
                    "error": str(e)
                }
                results["status"] = "partial_failure"
                logger.error(f"Exception executing task '{task.description}': {e}")
        
        logger.info(f"Phase '{phase.name}' execution completed with status: {results['status']}")
        return results 