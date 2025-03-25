"""
Project Executor Module

This module provides functionality to execute tasks in a project by phase.
"""

import os
from typing import Dict, Any, List, Optional
from loguru import logger

from roboco.core.models.phase import Phase
from roboco.core.task_manager import TaskManager
from roboco.core.phase_executor import PhaseExecutor


class ProjectExecutor:
    """Executes tasks in a project by phase."""
    
    def __init__(self, project_dir: str):
        """Initialize the project executor.
        
        Args:
            project_dir: Directory of the project containing tasks.md
        """
        self.project_dir = project_dir
        self.task_manager = TaskManager()
        self.phase_executor = PhaseExecutor(project_dir)
        logger.debug(f"Initialized ProjectExecutor for project: {project_dir}")
    
    async def execute_project(self, phase_filter: Optional[str] = None) -> Dict[str, Any]:
        """Execute tasks in the project, optionally filtered by phase.
        
        Args:
            phase_filter: Optional name of a specific phase to execute
            
        Returns:
            Dictionary with execution results
        """
        # Get tasks.md path
        tasks_path = os.path.join(self.project_dir, "tasks.md")
        
        if not os.path.exists(tasks_path):
            error_msg = f"Tasks file not found at: {tasks_path}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Parse tasks.md into phases and tasks
        logger.info(f"Parsing tasks file: {tasks_path}")
        phases = self.task_manager.parse(tasks_path)
        
        if not phases:
            error_msg = "No phases found in tasks.md"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.info(f"Found {len(phases)} phases in tasks.md")
        
        # Filter phases if needed
        if phase_filter:
            logger.info(f"Filtering phases by: {phase_filter}")
            filtered_phases = [p for p in phases if p.name.lower() == phase_filter.lower()]
            if not filtered_phases:
                error_msg = f"Phase '{phase_filter}' not found"
                logger.error(error_msg)
                return {"error": error_msg}
            phases = filtered_phases
            logger.info(f"Filtered to {len(phases)} phases")
        
        # Execute each phase sequentially
        results = {
            "phases": {},
            "overall_status": "success"
        }
        
        logger.info(f"Starting execution of {len(phases)} phases")
        
        for phase in phases:
            logger.info(f"Executing phase: {phase.name}")
            
            phase_result = await self.phase_executor.execute_phase(
                phase, 
                self.task_manager, 
                tasks_path
            )
            
            results["phases"][phase.name] = phase_result
            
            # Update overall status if any phase failed
            if phase_result["status"] != "success":
                results["overall_status"] = "partial_failure"
        
        logger.info(f"Project execution completed with status: {results['overall_status']}")
        return results
        
    async def execute_task(self, task_title: str) -> Dict[str, Any]:
        """Execute a specific task by title.
        
        Args:
            task_title: Title of the task to execute
            
        Returns:
            Dictionary with execution results
        """
        # Get tasks.md path
        tasks_path = os.path.join(self.project_dir, "tasks.md")
        
        if not os.path.exists(tasks_path):
            error_msg = f"Tasks file not found at: {tasks_path}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Parse tasks.md into phases and tasks
        logger.info(f"Parsing tasks file: {tasks_path}")
        phases = self.task_manager.parse(tasks_path)
        
        if not phases:
            error_msg = "No phases found in tasks.md"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Find the task in any phase
        for phase in phases:
            for task in phase.tasks:
                if task.title.lower() == task_title.lower():
                    logger.info(f"Found task '{task_title}' in phase '{phase.name}'")
                    
                    # Create a temporary phase with just this task
                    temp_phase = Phase(
                        name=phase.name,
                        tasks=[task],
                        status=phase.status
                    )
                    
                    # Execute just this task's phase
                    result = await self.phase_executor.execute_phase(
                        temp_phase,
                        self.task_manager,
                        tasks_path
                    )
                    
                    return {
                        "task": task_title,
                        "phase": phase.name,
                        "result": result
                    }
        
        # Task not found
        error_msg = f"Task '{task_title}' not found in any phase"
        logger.error(error_msg)
        return {"error": error_msg} 