"""
Project Service

This module provides services for managing projects, including project creation,
updating, and management of project-related operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import logging

from roboco.core.models import Project
from roboco.core.project_fs import ProjectFS, ProjectNotFoundError, get_project_fs


class ProjectService:
    """
    Service for managing projects.
    
    This service provides methods for creating, retrieving, updating, and
    deleting projects, as well as for managing project tasks.
    """

    def __init__(self):
        """
        Initialize the project service.
        """
        pass

    async def get_project(self, project_id: str) -> Project:
        """
        Retrieve a project by its ID.
        
        Args:
            project_id: The ID of the project to retrieve.
            
        Returns:
            The Project with the specified ID.
            
        Raises:
            Exception: If the project cannot be found.
        """
        try:
            project_fs = await ProjectFS.get_by_id(project_id)
            return await project_fs.get_project()
        except ProjectNotFoundError as e:
            raise Exception(f"Project not found: {str(e)}")
        except Exception as e:
            logger.error(f"Error retrieving project {project_id}: {str(e)}")
            raise Exception(f"Error retrieving project: {str(e)}")

    async def list_projects(self) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all projects.
        """
        try:
            return await ProjectFS.list_all()
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            raise Exception(f"Error listing projects: {str(e)}")

    async def create_project(
        self,
        name: str,
        description: str,
        directory: Optional[str] = None,
        teams: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Name of the project.
            description: Description of the project.
            directory: Custom directory name (optional).
            teams: Teams involved in the project (optional).
            tags: Tags for the project (optional).
            
        Returns:
            The newly created Project.
        """
        try:
            # Create the project using ProjectFS
            project_fs = await ProjectFS.create(
                name=name,
                description=description,
                directory=directory,
                teams=teams or [],
                tags=tags or []
            )
            
            # Return the project data
            return await project_fs.get_project()
            
        except Exception as e:
            logger.error(f"Error creating project {name}: {str(e)}")
            raise Exception(f"Error creating project: {str(e)}")

    async def update_project(self, project_id: str, **kwargs) -> Project:
        """
        Update a project.
        
        Args:
            project_id: The ID of the project to update.
            **kwargs: Project attributes to update.
            
        Returns:
            The updated Project.
            
        Raises:
            Exception: If the project cannot be found or updated.
        """
        try:
            # Get the project
            project_fs = await ProjectFS.get_by_id(project_id)
            project = await project_fs.get_project()
            
            # Update project attributes
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            # Save the project
            await project_fs.save_project(project)
            
            # Return the updated project
            return project
            
        except ProjectNotFoundError:
            raise Exception(f"Project not found: {project_id}")
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            raise Exception(f"Error updating project: {str(e)}")

    async def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: The ID of the project to delete.
            
        Returns:
            True if the project was deleted, False otherwise.
            
        Raises:
            Exception: If an error occurs during deletion.
        """
        try:
            # Get the project
            project_fs = await ProjectFS.get_by_id(project_id)
            
            # Delete the project
            success = await project_fs.delete()
            
            if not success:
                raise Exception(f"Failed to delete project {project_id}")
                
            return True
            
        except ProjectNotFoundError:
            # If the project doesn't exist, consider it deleted
            return True
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            raise Exception(f"Error deleting project: {str(e)}")

    async def find_projects_by_name(self, name: str) -> List[Project]:
        """
        Find projects by name.
        
        Args:
            name: Name to search for (case-insensitive partial match).
            
        Returns:
            List of projects matching the name.
        """
        try:
            return await ProjectFS.find_by_name(name)
        except Exception as e:
            logger.error(f"Error finding projects by name {name}: {str(e)}")
            raise Exception(f"Error finding projects by name: {str(e)}")

    async def find_projects_by_tag(self, tag: str) -> List[Project]:
        """
        Find projects by tag.
        
        Args:
            tag: Tag to search for (exact match).
            
        Returns:
            List of projects with the specified tag.
        """
        try:
            return await ProjectFS.find_by_tag(tag)
        except Exception as e:
            logger.error(f"Error finding projects by tag {tag}: {str(e)}")
            raise Exception(f"Error finding projects by tag: {str(e)}")

    async def add_task_to_project(self, project_id: str, task: Task) -> Project:
        """
        Add a task to a project.
        
        Args:
            project_id: The ID of the project to add the task to.
            task: The task to add.
            
        Returns:
            The updated Project.
            
        Raises:
            Exception: If the project cannot be found or updated.
        """
        try:
            # Get the project
            project_fs = await ProjectFS.get_by_id(project_id)
            
            # Add the task
            await project_fs.add_task(task)
            
            # Return the updated project
            return await project_fs.get_project()
            
        except ProjectNotFoundError:
            raise Exception(f"Project not found: {project_id}")
        except Exception as e:
            logger.error(f"Error adding task to project {project_id}: {str(e)}")
            raise Exception(f"Error adding task to project: {str(e)}")

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
