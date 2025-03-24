"""
Project Service

This module provides the service layer for project management operations.
It orchestrates interactions between the domain models and repositories.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
from loguru import logger

from roboco.core.models.project import Project
from roboco.core.schema import Task
from roboco.core.repositories.project_repository import ProjectRepository


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
    
    async def add_task_to_project(
        self,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        status: str = "TODO",
        assigned_to: Optional[str] = None,
        priority: str = "medium",
        tags: Optional[List[str]] = None
    ) -> str:
        """Add a task to a project.
        
        Args:
            project_id: ID of the project to add the task to
            title: Title of the task
            description: Description of the task
            status: Status of the task (TODO, IN_PROGRESS, DONE)
            assigned_to: Agent or person assigned to the task
            priority: Priority level (low, medium, high, critical)
            tags: Tags for categorizing the task
            
        Returns:
            ID of the project
            
        Raises:
            ValueError: If the project does not exist
        """
        project = await self.project_repository.get_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID {project_id} does not exist")
            
        task = Task(
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to,
            priority=priority,
            tags=tags or []
        )
        
        project.add_task(task)
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
