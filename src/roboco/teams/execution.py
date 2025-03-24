"""
Orchestration for executing tasks.
"""
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from roboco.core.models.phase import Phase
from roboco.core.value_objects.phase_status import PhaseStatus
from roboco.core.value_objects.task_status import TaskStatus
from roboco.core.models.execution import ExecutionState
from roboco.core.value_objects.execution_status import ExecutionStatus
from roboco.core.schema import Task
from roboco.core.task_manager import TaskManager
from roboco.core.team_factory import TeamFactory

logger = logging.getLogger(__name__)


class ExecutionOrchestrator:
    """Orchestrates the execution of phases and tasks, handling dependencies and updates."""
    
    def __init__(self):
        self.state = ExecutionState()
        self.team_factory = TeamFactory()
    
    async def execute_phases(self, phases: List[Phase], task_manager: TaskManager, tasks_path: str, project_dir: str) -> Dict[str, Any]:
        """Execute all phases in order, updating the tasks file after each task.
        
        Args:
            phases: List of phases to execute
            task_manager: Manager for updating the tasks file
            tasks_path: Path to the tasks file
            project_dir: Directory of the project
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        
        results = {
            "phases": [],
            "overall_success": True,
            "execution_time": 0
        }
        
        # Update state for UI
        self.state.status = ExecutionStatus.RUNNING
        self.state.last_updated = datetime.now()
        
        # Log execution start
        self.state.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "EXECUTION_STARTED",
            "phases": [p.name for p in phases]
        })
        
        for phase in phases:
            # Skip completed phases
            if phase.status == PhaseStatus.DONE:
                results["phases"].append({
                    "name": phase.name,
                    "status": "DONE",
                    "skipped": True,
                    "tasks": []
                })
                continue
            
            phase_result = await self.execute_phase(phase, task_manager, tasks_path, project_dir)
            results["phases"].append(phase_result)
            
            if not phase_result["success"]:
                results["overall_success"] = False
                
                # Update state for UI
                self.state.status = ExecutionStatus.FAILED
                self.state.last_updated = datetime.now()
                
                # Log execution failure
                self.state.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "EXECUTION_FAILED",
                    "phase": phase.name
                })
                
                break
        
        # Calculate total execution time
        results["execution_time"] = time.time() - start_time
        
        # Update state for UI if successful
        if results["overall_success"]:
            self.state.status = ExecutionStatus.COMPLETED
            self.state.last_updated = datetime.now()
            
            # Log execution completion
            self.state.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "EXECUTION_COMPLETED",
                "execution_time": results["execution_time"]
            })
        
        return results
    
    async def execute_phase(self, phase: Phase, task_manager: TaskManager, tasks_path: str, project_dir: str) -> Dict[str, Any]:
        """Execute all tasks in a phase, updating the tasks file after each task.
        
        Args:
            phase: Phase to execute
            task_manager: Manager for updating the tasks file
            tasks_path: Path to the tasks file
            project_dir: Directory of the project
            
        Returns:
            Dictionary with phase execution results
        """
        start_time = time.time()
        
        phase_result = {
            "name": phase.name,
            "tasks": [],
            "success": True,
            "execution_time": 0
        }
        
        # Update state for UI
        self.state.current_phase = phase.name
        self.state.current_task = None
        self.state.last_updated = datetime.now()
        
        # Log phase start
        self.state.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "PHASE_STARTED",
            "phase": phase.name
        })
        
        # Update phase status to IN_PROGRESS
        phase.status = PhaseStatus.IN_PROGRESS
        task_manager.update_tasks_file(tasks_path, [phase])
        
        # Create a team for this specific phase
        team = self.team_factory.create_team_for_phase(phase, project_dir)
        
        # Execute tasks with the specialized team
        for task in phase.tasks:
            # Skip completed tasks
            if task.status == TaskStatus.DONE:
                phase_result["tasks"].append({
                    "title": task.title,
                    "status": "DONE",
                    "skipped": True
                })
                continue
            
            # Update state for UI
            self.state.current_task = task.title
            self.state.last_updated = datetime.now()
            
            # Log task start
            self.state.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "TASK_STARTED",
                "phase": phase.name,
                "task": task.title
            })
            
            # Execute task (placeholder for now)
            task_start_time = time.time()
            logger.info(f"Executing task: {task.title}")
            
            # This would be replaced with actual task execution
            task_success = True
            task_output = f"Executed task: {task.title}"
            task_error = None
            
            task_execution_time = time.time() - task_start_time
            
            # Update task status based on result
            if task_success:
                task.status = TaskStatus.DONE
                task.completed_at = datetime.now()
                
                # Log task completion
                self.state.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "TASK_COMPLETED",
                    "phase": phase.name,
                    "task": task.title,
                    "execution_time": task_execution_time
                })
            else:
                task.status = TaskStatus.FAILED
                
                # Log task failure
                self.state.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "TASK_FAILED",
                    "phase": phase.name,
                    "task": task.title,
                    "error": task_error
                })
            
            # Update tasks file immediately
            task_manager.update_tasks_file(tasks_path, [phase])
            
            # Record result
            phase_result["tasks"].append({
                "title": task.title,
                "status": task.status,
                "execution_time": task_execution_time,
                "output": task_output,
                "error": task_error
            })
            
            # Stop phase execution if task failed
            if not task_success:
                phase_result["success"] = False
                
                # Log phase failure
                self.state.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "PHASE_FAILED",
                    "phase": phase.name,
                    "task": task.title
                })
                
                break
        
        # Update phase status if all tasks completed
        if all(task.status == TaskStatus.DONE for task in phase.tasks):
            phase.status = PhaseStatus.DONE
            
            # Log phase completion
            self.state.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "PHASE_COMPLETED",
                "phase": phase.name
            })
        
        # Update tasks file
        task_manager.update_tasks_file(tasks_path, [phase])
        
        # Calculate phase execution time
        phase_result["execution_time"] = time.time() - start_time
        
        # Update progress information for UI
        completed_tasks = sum(1 for t in phase.tasks if t.status == TaskStatus.DONE)
        total_tasks = len(phase.tasks)
        self.state.progress[phase.name] = {
            "completed": completed_tasks,
            "total": total_tasks,
            "percentage": round((completed_tasks / total_tasks) * 100, 2) if total_tasks > 0 else 0
        }
        
        # Update state for UI
        self.state.current_task = None
        self.state.last_updated = datetime.now()
        
        return phase_result


class ExecutionTeam:
    """Team responsible for executing tasks generated by the PlanningTeam."""
    
    def __init__(self, project_dir: str):
        """Initialize the execution team.
        
        Args:
            project_dir: Directory of the project
        """
        self.project_dir = project_dir
        self.task_manager = TaskManager()
        self.orchestrator = ExecutionOrchestrator()
    
    async def execute_project(self, phase_filter: Optional[str] = None) -> Dict[str, Any]:
        """Execute all tasks in the project, optionally filtered by phase.
        
        Args:
            phase_filter: Optional name of a specific phase to execute
            
        Returns:
            Dictionary with execution results
        """
        # Get tasks.md path
        tasks_path = os.path.join(self.project_dir, "tasks.md")
        
        # Parse tasks.md into phases and tasks
        phases = self.task_manager.parse(tasks_path)
        
        if not phases:
            return {"error": "No phases found in tasks.md"}
        
        # Filter phases if needed
        if phase_filter:
            filtered_phases = [p for p in phases if p.name.lower() == phase_filter.lower()]
            if not filtered_phases:
                return {"error": f"Phase '{phase_filter}' not found"}
            phases = filtered_phases
        
        # Execute phases
        results = await self.orchestrator.execute_phases(
            phases, 
            self.task_manager, 
            tasks_path, 
            self.project_dir
        )
        
        return results
    
    async def execute_single_task(self, phase_name: str, task_title: str) -> Dict[str, Any]:
        """Execute a single task by phase name and task title.
        
        Args:
            phase_name: Name of the phase containing the task
            task_title: Title of the task to execute
            
        Returns:
            Dictionary with task execution results
        """
        # Get tasks.md path
        tasks_path = os.path.join(self.project_dir, "tasks.md")
        
        # Parse tasks.md into phases and tasks
        phases = self.task_manager.parse(tasks_path)
        
        # Find the specified phase
        phase = self.task_manager.get_phase_by_name(phases, phase_name)
        if not phase:
            return {"error": f"Phase '{phase_name}' not found"}
        
        # Find the specified task
        task = next((t for t in phase.tasks if t.title.lower() == task_title.lower()), None)
        if not task:
            return {"error": f"Task '{task_title}' not found in phase '{phase_name}'"}
        
        # Update state for UI
        self.orchestrator.state.current_phase = phase.name
        self.orchestrator.state.current_task = task.title
        self.orchestrator.state.status = ExecutionStatus.RUNNING
        self.orchestrator.state.last_updated = datetime.now()
        
        # Log task start
        self.orchestrator.state.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": "TASK_STARTED",
            "phase": phase.name,
            "task": task.title
        })
        
        # Execute task (placeholder for now)
        start_time = time.time()
        logger.info(f"Executing single task: {task.title}")
        
        # This would be replaced with actual task execution
        task_success = True
        task_output = f"Executed task: {task.title}"
        task_error = None
        
        execution_time = time.time() - start_time
        
        # Update task status based on result
        if task_success:
            task.status = TaskStatus.DONE
            task.completed_at = datetime.now()
            
            # Log task completion
            self.orchestrator.state.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "TASK_COMPLETED",
                "phase": phase.name,
                "task": task.title,
                "execution_time": execution_time
            })
        else:
            task.status = TaskStatus.FAILED
            
            # Log task failure
            self.orchestrator.state.execution_log.append({
                "timestamp": datetime.now().isoformat(),
                "event": "TASK_FAILED",
                "phase": phase.name,
                "task": task.title,
                "error": task_error
            })
        
        # Update tasks file
        self.task_manager.update_tasks_file(tasks_path, [phase])
        
        # Update state for UI
        self.orchestrator.state.status = ExecutionStatus.COMPLETED if task_success else ExecutionStatus.FAILED
        self.orchestrator.state.last_updated = datetime.now()
        
        return {
            "phase": phase_name,
            "task": task_title,
            "success": task_success,
            "output": task_output,
            "error": task_error,
            "execution_time": execution_time
        }
    
    def get_current_state(self) -> ExecutionState:
        """Get the current execution state for UI display.
        
        Returns:
            Current execution state
        """
        return self.orchestrator.state
    
    def get_execution_progress(self) -> Dict[str, Any]:
        """Get a summary of execution progress for UI display.
        
        Returns:
            Dictionary with execution progress information
        """
        return {
            "current_phase": self.orchestrator.state.current_phase,
            "current_task": self.orchestrator.state.current_task,
            "status": self.orchestrator.state.status,
            "progress": self.orchestrator.state.progress,
            "last_updated": self.orchestrator.state.last_updated.isoformat()
        }
