"""
Task Service

This module provides services for managing tasks, including task creation,
updating, and management of task-related operations.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
from loguru import logger

from roboco.core.models import Task
from roboco.core.task_manager import TaskManager
from roboco.core.repositories.project_repository import ProjectRepository


class TaskService:
    """
    Service for managing tasks and task-related operations.
    
    This service follows the DDD principles by encapsulating task-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self, project_repository: ProjectRepository, task_manager: Optional[TaskManager] = None):
        """
        Initialize the task service with its dependencies.
        
        Args:
            project_repository: Repository for project data access
            task_manager: Manager for task file operations (optional)
        """
        self.project_repository = project_repository
        self.task_manager = task_manager or TaskManager()
    
    async def get_tasks_for_project(self, project_id: str) -> List[Task]:
        """
        Get all tasks for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            List of tasks for the project
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        return project.tasks
    
    async def get_task(self, project_id: str, task_id: str) -> Optional[Task]:
        """
        Get a specific task from a project.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            
        Returns:
            The task if found, None otherwise
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        for task in project.tasks:
            if getattr(task, 'id', None) == task_id:
                return task
                
        return None
    
    async def create_task(
        self,
        project_id: str,
        description: Optional[str] = None,
        status: str = "TODO",
        assigned_to: Optional[str] = None,
        priority: str = "medium",
        depends_on: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Task:
        """
        Create a new task in a project.
        
        Args:
            project_id: ID of the project
            description: Description of the task
            status: Status of the task (TODO, IN_PROGRESS, DONE)
            assigned_to: Agent or person assigned to the task
            priority: Priority level (low, medium, high, critical)
            depends_on: IDs of tasks this task depends on
            tags: Tags for categorizing the task
            
        Returns:
            The created task
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        task = Task(
            id=str(uuid.uuid4()),
            description=description,
            status=status,
            assigned_to=assigned_to,
            priority=priority,
            depends_on=depends_on or [],
            tags=tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed_at=None
        )
        
        project.add_task(task)
        await self.project_repository.save(project)
        
        return task
    
    async def update_task(
        self,
        project_id: str,
        task_id: str,
        description: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        priority: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> Task:
        """
        Update an existing task in a project.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to update
            description: New description of the task
            status: New status of the task
            assigned_to: New assignee of the task
            priority: New priority of the task
            depends_on: New dependencies of the task
            tags: New tags for the task
            
        Returns:
            The updated task
            
        Raises:
            ValueError: If the project or task does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        # Find the task to update
        task_to_update = None
        task_index = -1
        
        for i, task in enumerate(project.tasks):
            if getattr(task, 'id', None) == task_id:
                task_to_update = task
                task_index = i
                break
                
        if not task_to_update:
            raise ValueError(f"Task with ID {task_id} does not exist in project {project_id}")
            
        if description is not None:
            task_to_update.description = description
            
        if status is not None:
            old_status = task_to_update.status
            task_to_update.status = status
            
            # If the task is being marked as done, set the completed_at timestamp
            if status.upper() == "DONE" and old_status.upper() != "DONE":
                task_to_update.completed_at = datetime.now()
            # If the task is being moved from done to another status, clear the completed_at timestamp
            elif status.upper() != "DONE" and old_status.upper() == "DONE":
                task_to_update.completed_at = None
                
        if assigned_to is not None:
            task_to_update.assigned_to = assigned_to
            
        if priority is not None:
            task_to_update.priority = priority
            
        if depends_on is not None:
            task_to_update.depends_on = depends_on
            
        if tags is not None:
            task_to_update.tags = tags
            
        task_to_update.updated_at = datetime.now()
        
        # Update the task in the project
        project.tasks[task_index] = task_to_update
        await self.project_repository.save(project)
        
        return task_to_update
    
    async def delete_task(self, project_id: str, task_id: str) -> bool:
        """
        Delete a task from a project.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task to delete
            
        Returns:
            True if the task was deleted, False otherwise
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        # Find the task to delete
        task_index = -1
        
        for i, task in enumerate(project.tasks):
            if getattr(task, 'id', None) == task_id:
                task_index = i
                break
                
        if task_index == -1:
            return False
            
        # Remove the task from the project
        project.tasks.pop(task_index)
        await self.project_repository.save(project)
        
        return True
    
    async def get_tasks_by_status(self, project_id: str, status: str) -> List[Task]:
        """
        Get all tasks with a specific status from a project.
        
        Args:
            project_id: ID of the project
            status: Status to filter by
            
        Returns:
            List of tasks with the specified status
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        return [task for task in project.tasks if task.status.upper() == status.upper()]
    
    async def get_tasks_by_assignee(self, project_id: str, assignee: str) -> List[Task]:
        """
        Get all tasks assigned to a specific person or agent.
        
        Args:
            project_id: ID of the project
            assignee: Name of the assignee
            
        Returns:
            List of tasks assigned to the specified person or agent
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        return [task for task in project.tasks if task.assigned_to == assignee]
    
    async def get_tasks_by_priority(self, project_id: str, priority: str) -> List[Task]:
        """
        Get all tasks with a specific priority from a project.
        
        Args:
            project_id: ID of the project
            priority: Priority to filter by
            
        Returns:
            List of tasks with the specified priority
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        return [task for task in project.tasks if task.priority.lower() == priority.lower()]
    
    async def get_tasks_by_tag(self, project_id: str, tag: str) -> List[Task]:
        """
        Get all tasks with a specific tag from a project.
        
        Args:
            project_id: ID of the project
            tag: Tag to filter by
            
        Returns:
            List of tasks with the specified tag
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        return [task for task in project.tasks if tag in task.tags]
    
    async def import_tasks_from_file(self, project_id: str, tasks_file_path: str) -> List[Task]:
        """
        Import tasks from a tasks.md file into a project.
        
        Args:
            project_id: ID of the project
            tasks_file_path: Path to the tasks.md file
            
        Returns:
            List of imported tasks
            
        Raises:
            ValueError: If the project does not exist or the file cannot be parsed
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        try:
            # Parse the tasks file
            phases = self.task_manager.parse(tasks_file_path)
            
            # Extract tasks from all phases
            imported_tasks = []
            for phase in phases:
                for task in phase.tasks:
                    # Add a unique ID to the task
                    task_id = getattr(task, 'id', None) or str(uuid.uuid4())
                    setattr(task, 'id', task_id)
                    
                    # Add the task to the project
                    project.add_task(task)
                    imported_tasks.append(task)
            
            # Save the updated project
            await self.project_repository.save(project)
            
            return imported_tasks
        except Exception as e:
            logger.error(f"Error importing tasks from file: {e}")
            raise ValueError(f"Failed to import tasks from file: {e}")
    
    async def export_tasks_to_file(self, project_id: str, tasks_file_path: str) -> bool:
        """
        Export tasks from a project to a tasks.md file.
        
        Args:
            project_id: ID of the project
            tasks_file_path: Path to save the tasks.md file
            
        Returns:
            True if the export was successful, False otherwise
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        try:
            # Group tasks by status to create phases
            todo_tasks = [task for task in project.tasks if task.status.upper() == "TODO"]
            in_progress_tasks = [task for task in project.tasks if task.status.upper() == "IN_PROGRESS"]
            done_tasks = [task for task in project.tasks if task.status.upper() == "DONE"]
            
            # Create phases
            from roboco.core.models.phase import Phase, PhaseStatus
            
            phases = [
                Phase(name="To Do", tasks=todo_tasks, status=PhaseStatus.NOT_STARTED),
                Phase(name="In Progress", tasks=in_progress_tasks, status=PhaseStatus.IN_PROGRESS),
                Phase(name="Done", tasks=done_tasks, status=PhaseStatus.COMPLETED)
            ]
            
            # Export the phases to the file
            self.task_manager.update(tasks_file_path, phases)
            
            return True
        except Exception as e:
            logger.error(f"Error exporting tasks to file: {e}")
            return False
