"""
Sprint Service

This module provides services for managing sprints, including sprint creation,
updating, and management of sprint-related operations.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
from loguru import logger

from roboco.domain.models.sprint import Sprint
from roboco.domain.models.todo_item import TodoItem
from roboco.domain.repositories.project_repository import ProjectRepository


class SprintService:
    """
    Service for managing sprints and sprint-related operations.
    
    This service follows the DDD principles by encapsulating sprint-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize the sprint service with its dependencies.
        
        Args:
            project_repository: Repository for project data access
        """
        self.project_repository = project_repository
    
    async def create_sprint(self, project_id: str, name: str, description: str, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           status: str = "planned") -> Sprint:
        """
        Create a new sprint for a project.
        
        Args:
            project_id: ID of the project to create the sprint for
            name: Name of the sprint
            description: Description of the sprint
            start_date: Optional start date
            end_date: Optional end date
            status: Sprint status (default: "planned")
            
        Returns:
            The created Sprint domain object
            
        Raises:
            ValueError: If the project is not found or the sprint name already exists
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Check if a sprint with the same name already exists
        for existing_sprint in project.sprints:
            if existing_sprint.name == name:
                raise ValueError(f"Sprint with name '{name}' already exists in project {project_id}")
        
        # Create the sprint
        sprint = Sprint(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status
        )
        
        # Add the sprint to the project
        project.add_sprint(sprint)
        
        # Save the project
        await self.project_repository.update_project(project)
        
        return sprint
    
    async def get_sprint(self, project_id: str, sprint_name: str) -> Sprint:
        """
        Get a sprint by name from a project.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            The Sprint domain object
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Find the sprint
        for sprint in project.sprints:
            if sprint.name == sprint_name:
                return sprint
        
        raise ValueError(f"Sprint with name '{sprint_name}' not found in project {project_id}")
    
    async def update_sprint(self, project_id: str, sprint_name: str, 
                           name: Optional[str] = None,
                           description: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           status: Optional[str] = None) -> Sprint:
        """
        Update a sprint in a project.
        
        Args:
            project_id: ID of the project
            sprint_name: Current name of the sprint
            name: Optional new name for the sprint
            description: Optional new description
            start_date: Optional new start date
            end_date: Optional new end date
            status: Optional new status
            
        Returns:
            The updated Sprint domain object
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Find the sprint
        sprint = None
        for s in project.sprints:
            if s.name == sprint_name:
                sprint = s
                break
        
        if not sprint:
            raise ValueError(f"Sprint with name '{sprint_name}' not found in project {project_id}")
        
        # Check if the new name would conflict with an existing sprint
        if name and name != sprint_name:
            for s in project.sprints:
                if s.name == name:
                    raise ValueError(f"Sprint with name '{name}' already exists in project {project_id}")
        
        # Update the sprint
        if name:
            sprint.name = name
        if description:
            sprint.description = description
        if start_date:
            sprint.start_date = start_date
        if end_date:
            sprint.end_date = end_date
        if status:
            sprint.status = status
        
        # Save the project
        await self.project_repository.update_project(project)
        
        return sprint
    
    async def delete_sprint(self, project_id: str, sprint_name: str) -> bool:
        """
        Delete a sprint from a project.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            True if the sprint was deleted, False otherwise
            
        Raises:
            ValueError: If the project is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Find the sprint
        sprint_index = None
        for i, sprint in enumerate(project.sprints):
            if sprint.name == sprint_name:
                sprint_index = i
                break
        
        if sprint_index is None:
            return False
        
        # Remove the sprint
        project.sprints.pop(sprint_index)
        
        # Save the project
        await self.project_repository.update_project(project)
        
        return True
    
    async def list_sprints(self, project_id: str, status_filter: Optional[str] = None) -> List[Sprint]:
        """
        List all sprints in a project, optionally filtered by status.
        
        Args:
            project_id: ID of the project
            status_filter: Optional status to filter by
            
        Returns:
            List of Sprint domain objects
            
        Raises:
            ValueError: If the project is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Filter sprints if needed
        if status_filter:
            return [sprint for sprint in project.sprints if sprint.status == status_filter]
        
        return project.sprints
    
    async def add_todo_to_sprint(self, project_id: str, sprint_name: str, todo_item: TodoItem) -> TodoItem:
        """
        Add a todo item to a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            todo_item: The todo item to add
            
        Returns:
            The added TodoItem domain object
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Find the sprint
        sprint = None
        for s in project.sprints:
            if s.name == sprint_name:
                sprint = s
                break
        
        if not sprint:
            raise ValueError(f"Sprint with name '{sprint_name}' not found in project {project_id}")
        
        # Set the sprint name on the todo item
        todo_item.sprint = sprint_name
        
        # Add the todo item to the project
        project.add_todo(todo_item)
        
        # Save the project
        await self.project_repository.update_project(project)
        
        return todo_item
    
    async def move_todo_to_sprint(self, project_id: str, todo_title: str, 
                                 target_sprint_name: str) -> TodoItem:
        """
        Move a todo item to a different sprint.
        
        Args:
            project_id: ID of the project
            todo_title: Title of the todo item
            target_sprint_name: Name of the target sprint
            
        Returns:
            The updated TodoItem domain object
            
        Raises:
            ValueError: If the project, todo item, or target sprint is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Find the todo item
        todo_item = None
        for todo in project.todos:
            if todo.title == todo_title:
                todo_item = todo
                break
        
        if not todo_item:
            raise ValueError(f"Todo item with title '{todo_title}' not found in project {project_id}")
        
        # Verify the target sprint exists
        target_sprint_exists = False
        for sprint in project.sprints:
            if sprint.name == target_sprint_name:
                target_sprint_exists = True
                break
        
        if not target_sprint_exists:
            raise ValueError(f"Sprint with name '{target_sprint_name}' not found in project {project_id}")
        
        # Update the todo item's sprint
        todo_item.sprint = target_sprint_name
        
        # Save the project
        await self.project_repository.update_project(project)
        
        return todo_item
    
    async def get_sprint_todos(self, project_id: str, sprint_name: str, 
                              status_filter: Optional[str] = None) -> List[TodoItem]:
        """
        Get all todo items for a sprint, optionally filtered by status.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            status_filter: Optional status to filter by
            
        Returns:
            List of TodoItem domain objects
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the project
        project = await self.project_repository.get_project(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} not found")
        
        # Verify the sprint exists
        sprint_exists = False
        for sprint in project.sprints:
            if sprint.name == sprint_name:
                sprint_exists = True
                break
        
        if not sprint_exists:
            raise ValueError(f"Sprint with name '{sprint_name}' not found in project {project_id}")
        
        # Get todos for the sprint
        sprint_todos = [todo for todo in project.todos if todo.sprint == sprint_name]
        
        # Apply status filter if needed
        if status_filter:
            sprint_todos = [todo for todo in sprint_todos if todo.status == status_filter]
        
        return sprint_todos
    
    async def start_sprint(self, project_id: str, sprint_name: str) -> Sprint:
        """
        Start a sprint by changing its status to "in_progress" and setting the start date.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            The updated Sprint domain object
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the sprint
        sprint = await self.get_sprint(project_id, sprint_name)
        
        # Update the sprint
        sprint.status = "in_progress"
        if not sprint.start_date:
            sprint.start_date = datetime.now()
        
        # Save the changes
        await self.update_sprint(
            project_id=project_id,
            sprint_name=sprint_name,
            status=sprint.status,
            start_date=sprint.start_date
        )
        
        return sprint
    
    async def complete_sprint(self, project_id: str, sprint_name: str) -> Sprint:
        """
        Complete a sprint by changing its status to "completed" and setting the end date.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            The updated Sprint domain object
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the sprint
        sprint = await self.get_sprint(project_id, sprint_name)
        
        # Update the sprint
        sprint.status = "completed"
        sprint.end_date = datetime.now()
        
        # Save the changes
        await self.update_sprint(
            project_id=project_id,
            sprint_name=sprint_name,
            status=sprint.status,
            end_date=sprint.end_date
        )
        
        return sprint
    
    async def get_sprint_progress(self, project_id: str, sprint_name: str) -> Dict[str, Any]:
        """
        Get progress statistics for a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint
            
        Returns:
            Dictionary with progress statistics
            
        Raises:
            ValueError: If the project or sprint is not found
        """
        # Get the sprint todos
        todos = await self.get_sprint_todos(project_id, sprint_name)
        
        # Calculate statistics
        total_todos = len(todos)
        completed_todos = len([todo for todo in todos if todo.status == "completed"])
        in_progress_todos = len([todo for todo in todos if todo.status == "in_progress"])
        
        # Calculate completion percentage
        completion_percentage = 0
        if total_todos > 0:
            completion_percentage = (completed_todos / total_todos) * 100
        
        return {
            "total_todos": total_todos,
            "completed_todos": completed_todos,
            "in_progress_todos": in_progress_todos,
            "completion_percentage": completion_percentage,
            "sprint_name": sprint_name,
            "project_id": project_id
        }
