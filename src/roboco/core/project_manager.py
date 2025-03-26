"""
Project Manager Module

This module provides functionality for managing projects, including their tasks
and associated teams and jobs.
"""

from datetime import datetime
import os
import json

from loguru import logger

from roboco.core.models.project import Project
from roboco.core.project_fs import ProjectFS
from roboco.core.config import load_config, get_workspace


class ProjectManager:
    """
    Manager for handling projects, tasks, and teams.
    
    This class provides methods for creating, retrieving, and updating projects,
    as well as for managing project tasks and configuration.
    """
    
    def __init__(self, config=None):
        """
        Initialize the project manager.
        
        Args:
            config: Configuration object
        """
        self.config = config or load_config()
        self.projects = []
        self._load_projects()
    
    def _load_projects(self):
        """
        Load projects from disk.
        """
        try:
            # Get the workspace base path
            workspace_base = get_workspace(self.config)
            
            # Create the workspace directory if it doesn't exist
            if not os.path.exists(workspace_base):
                os.makedirs(workspace_base, exist_ok=True)
                return
            
            # Iterate through project directories
            for project_dir in os.listdir(workspace_base):
                dir_path = os.path.join(workspace_base, project_dir)
                
                if os.path.isdir(dir_path):
                    project_file = os.path.join(dir_path, "project.json")
                    
                    if os.path.exists(project_file):
                        try:
                            with open(project_file, "r") as f:
                                project_data = json.load(f)
                                project = Project.from_dict(project_data)
                                self.projects.append(project)
                        except Exception as e:
                            logger.error(f"Failed to load project from {project_file}: {str(e)}")
        except Exception as e:
            logger.error(f"Error loading projects: {str(e)}")
    
    async def _save_project(self, project):
        """
        Save a project to disk.
        
        Args:
            project: Project to save
        """
        try:
            # Create a ProjectFS instance for the project
            project_fs = await ProjectFS.get_by_id(project.id)
            
            # Save the project
            await project_fs.save_project(project)
            
        except Exception as e:
            logger.error(f"Error saving project {project.id}: {str(e)}")
            raise Exception(f"Error saving project: {str(e)}")
    
    async def _update_task_markdown(self, project):
        """
        Update the task markdown file for a project.
        
        This is now handled internally by ProjectFS.save_project().
        
        Args:
            project: Project to update task markdown for
        """
        # This is now managed by the ProjectFS abstraction
        pass
    
    async def create_project(
        self,
        name,
        description,
        directory=None,
        teams=None,
        tags=None,
    ):
        """
        Create a new project.
        
        Args:
            name: Name of the project
            description: Description of the project
            directory: Optional directory name
            teams: List of teams involved in the project
            tags: Tags for the project
            
        Returns:
            The created project
        """
        try:
            # Create the project using ProjectFS
            project_fs = await ProjectFS.create(
                name=name,
                description=description,
                directory=directory,
                teams=teams,
                tags=tags
            )
            
            # Get the project and add it to our cache
            project = await project_fs.get_project()
            self.projects.append(project)
            
            return project
            
        except Exception as e:
            logger.error(f"Error creating project {name}: {str(e)}")
            raise Exception(f"Error creating project: {str(e)}")
    
    def get_project(self, project_id):
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project to get
            
        Returns:
            Project with the specified ID, or None if not found
        """
        for project in self.projects:
            if project.id == project_id:
                return project
        return None
    
    def list_projects(self):
        """
        List all projects.
        
        Returns:
            List of all projects
        """
        return self.projects
    
    def find_projects_by_name(self, name):
        """
        Find projects by name.
        
        Args:
            name: Name to search for
            
        Returns:
            List of projects matching the name
        """
        return [p for p in self.projects if name.lower() in p.name.lower()]
    
    def find_projects_by_tag(self, tag):
        """
        Find projects by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of projects with the specified tag
        """
        return [p for p in self.projects if tag in p.tags]
    
    async def update_project(self, project_id, **kwargs):
        """
        Update a project.
        
        Args:
            project_id: ID of the project to update
            **kwargs: Project attributes to update
            
        Returns:
            Updated project
            
        Raises:
            Exception: If the project is not found
        """
        project = self.get_project(project_id)
        if not project:
            raise Exception(f"Project not found: {project_id}")
        
        # Update project attributes
        for key, value in kwargs.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        # Save the project
        await self._save_project(project)
        
        return project
    
    async def add_task(self, project_id, task):
        """
        Add a task to a project.
        
        Args:
            project_id: ID of the project to add the task to
            task: Task to add
            
        Returns:
            Updated project
            
        Raises:
            Exception: If the project is not found
        """
        project = self.get_project(project_id)
        if not project:
            raise Exception(f"Project not found: {project_id}")
        
        # Add the task to the project
        project.tasks.append(task)
        
        # Save the project
        await self._save_project(project)
        
        return project
    
    async def update_task(self, project_id, task_id, **kwargs):
        """
        Update a task in a project.
        
        Args:
            project_id: ID of the project containing the task
            task_id: ID of the task to update
            **kwargs: Task attributes to update
            
        Returns:
            Updated project
            
        Raises:
            Exception: If the project or task is not found
        """
        project = self.get_project(project_id)
        if not project:
            raise Exception(f"Project not found: {project_id}")
        
        # Find the task
        task_found = False
        for task in project.tasks:
            if task.id == task_id:
                # Update task attributes
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # Special handling for status changes
                if kwargs.get("status") == "DONE" and not task.completed_at:
                    task.completed_at = datetime.now()
                
                task_found = True
                break
        
        if not task_found:
            raise Exception(f"Task not found: {task_id}")
        
        # Save the project
        await self._save_project(project)
        
        return project
    
    async def delete_project(self, project_id):
        """
        Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        # Find the project
        project = self.get_project(project_id)
        if not project:
            return True  # Already deleted
        
        try:
            # Delete the project using ProjectFS
            project_fs = await ProjectFS.get_by_id(project_id)
            success = await project_fs.delete()
            
            if success:
                # Remove from local cache
                self.projects = [p for p in self.projects if p.id != project_id]
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            return False