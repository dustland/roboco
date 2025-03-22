"""
Project Service

This module provides the service layer for project management operations.
It orchestrates interactions between the domain models and repositories.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from loguru import logger

from roboco.domain.models.project import Project
from roboco.domain.models.sprint import Sprint
from roboco.domain.models.todo_item import TodoItem
from roboco.domain.repositories.project_repository import ProjectRepository


class ProjectService:
    """Service for project management operations.
    
    This class provides high-level operations for managing projects,
    orchestrating interactions between domain models and repositories.
    """
    
    def __init__(self, project_repository: ProjectRepository):
        """Initialize the project service.
        
        Args:
            project_repository: Repository for project persistence
        """
        self.project_repository = project_repository
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by its ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            The project if found, None otherwise
        """
        return await self.project_repository.get_by_id(project_id)
    
    async def list_projects(self) -> List[Project]:
        """List all projects.
        
        Returns:
            List of all projects
        """
        return await self.project_repository.list_all()
    
    async def create_project(
        self, 
        name: str, 
        description: str, 
        directory: Optional[str] = None,
        teams: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Create a new project.
        
        Args:
            name: Name of the project
            description: Description of the project
            directory: Directory for project files (derived from name if not provided)
            teams: List of teams involved in the project
            tags: Tags for categorizing the project
            
        Returns:
            ID of the created project
        """
        project = Project(
            name=name,
            description=description,
            directory=directory,
            teams=teams or [],
            tags=tags or []
        )
        
        return await self.project_repository.save(project)
    
    async def update_project(self, project: Project) -> str:
        """Update an existing project.
        
        Args:
            project: The project to update
            
        Returns:
            ID of the updated project
            
        Raises:
            ValueError: If the project does not exist
        """
        existing_project = await self.project_repository.get_by_id(project.id)
        if not existing_project:
            raise ValueError(f"Project with ID {project.id} does not exist")
            
        return await self.project_repository.save(project)
    
    async def delete_project(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        return await self.project_repository.delete(project_id)
    
    async def find_projects_by_name(self, name: str) -> List[Project]:
        """Find projects by name.
        
        Args:
            name: Name to search for
            
        Returns:
            List of projects matching the name
        """
        return await self.project_repository.find_by_name(name)
    
    async def find_projects_by_tag(self, tag: str) -> List[Project]:
        """Find projects by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of projects with the specified tag
        """
        return await self.project_repository.find_by_tag(tag)
    
    async def add_sprint_to_project(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: str = "planned",
        tags: Optional[List[str]] = None
    ) -> str:
        """Add a sprint to a project.
        
        Args:
            project_id: ID of the project to add the sprint to
            name: Name of the sprint
            description: Description of the sprint
            start_date: Start date of the sprint
            end_date: End date of the sprint
            status: Status of the sprint (planned, active, completed)
            tags: Tags for categorizing the sprint
            
        Returns:
            ID of the project
            
        Raises:
            ValueError: If the project does not exist or a sprint with the same name already exists
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        # Check if a sprint with the same name already exists
        if any(s.name == name for s in project.sprints):
            raise ValueError(f"Sprint {name} already exists in project {project.name}")
            
        sprint = Sprint(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            tags=tags or []
        )
        
        project.add_sprint(sprint)
        await self.project_repository.save(project)
        
        return project_id
    
    async def add_todo_to_project(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        status: str = "TODO",
        assigned_to: Optional[str] = None,
        priority: str = "medium",
        sprint_name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """Add a todo item to a project.
        
        Args:
            project_id: ID of the project to add the todo to
            title: Title of the todo
            description: Description of the todo
            status: Status of the todo (TODO, IN_PROGRESS, DONE)
            assigned_to: Agent or person assigned to the todo
            priority: Priority level (low, medium, high, critical)
            sprint_name: Name of the sprint to add the todo to (if any)
            tags: Tags for categorizing the todo
            
        Returns:
            ID of the project
            
        Raises:
            ValueError: If the project does not exist or the specified sprint does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        todo = TodoItem(
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to,
            priority=priority,
            tags=tags or []
        )
        
        if sprint_name:
            # Find the sprint
            sprint = next((s for s in project.sprints if s.name == sprint_name), None)
            if not sprint:
                raise ValueError(f"Sprint {sprint_name} does not exist in project {project.name}")
                
            # Add the todo to the sprint
            sprint.add_todo(todo)
        else:
            # Add the todo to the project
            project.add_todo(todo)
        
        await self.project_repository.save(project)
        
        return project_id
    
    async def set_current_sprint(self, project_id: str, sprint_name: str) -> str:
        """Set the current active sprint for a project.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint to set as current
            
        Returns:
            ID of the project
            
        Raises:
            ValueError: If the project does not exist or the specified sprint does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        project.set_current_sprint(sprint_name)
        await self.project_repository.save(project)
        
        return project_id
    
    async def create_project_from_query(self, query: str, teams: Optional[List[str]] = None) -> str:
        """Create a project from a natural language query.
        
        This is a placeholder for future implementation that would use
        AI to parse the query and create a project with appropriate attributes.
        
        Args:
            query: Natural language description of the project
            teams: List of teams to assign to the project
            
        Returns:
            ID of the created project
        """
        # For now, just create a basic project with the query as the description
        name = f"Project from query: {query[:30]}..." if len(query) > 30 else f"Project from query: {query}"
        
        return await self.create_project(
            name=name,
            description=query,
            teams=teams
        )
