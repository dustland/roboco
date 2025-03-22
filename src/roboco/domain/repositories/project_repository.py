"""
Project Repository Interface

This module defines the interface for project repositories.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from roboco.domain.models.project import Project


class ProjectRepository(ABC):
    """Interface for project repositories.
    
    This abstract class defines the contract that all project repositories must implement.
    It provides methods for creating, retrieving, updating, and deleting projects.
    """
    
    @abstractmethod
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            The project if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_all(self) -> List[Project]:
        """List all projects.
        
        Returns:
            List of all projects
        """
        pass
    
    @abstractmethod
    async def save(self, project: Project) -> str:
        """Save a project.
        
        If the project already exists, it will be updated.
        If the project does not exist, it will be created.
        
        Args:
            project: The project to save
            
        Returns:
            The ID of the saved project
        """
        pass
    
    @abstractmethod
    async def delete(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> List[Project]:
        """Find projects by name.
        
        Args:
            name: Name to search for
            
        Returns:
            List of projects matching the name
        """
        pass
    
    @abstractmethod
    async def find_by_tag(self, tag: str) -> List[Project]:
        """Find projects by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of projects with the specified tag
        """
        pass
