"""
File-based Project Repository Implementation

This module implements the ProjectRepository interface using the file system for storage.
"""

import os
import json
import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
from loguru import logger

from roboco.domain.repositories.project_repository import ProjectRepository
from roboco.domain.models.project import Project
from roboco.domain.models.sprint import Sprint
from roboco.domain.models.todo_item import TodoItem
from roboco.core import config


class FileProjectRepository(ProjectRepository):
    """File-based implementation of the ProjectRepository interface.
    
    This class implements the ProjectRepository interface using the file system for storage.
    Projects are stored as JSON files in a directory structure.
    """
    
    def __init__(self, projects_dir: Optional[str] = None):
        """Initialize the file-based project repository.
        
        Args:
            projects_dir: Optional custom directory for storing projects
        """
        self.config = config.load_config()
        self.projects_dir = projects_dir or os.path.join(self.config.core.workspace_base, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        
    async def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get a project by its ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            The project if found, None otherwise
        """
        project_dir = os.path.join(self.projects_dir, project_id)
        config_path = os.path.join(project_dir, "project.json")
        
        if not os.path.exists(config_path):
            return None
            
        try:
            with open(config_path, "r") as f:
                project_data = json.load(f)
                return Project.from_dict(project_data)
        except Exception as e:
            logger.error(f"Failed to load project {project_id}: {str(e)}")
            return None
    
    async def list_all(self) -> List[Project]:
        """List all projects.
        
        Returns:
            List of all projects
        """
        projects = []
        
        for project_dir in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_dir)
            if os.path.isdir(project_path):
                config_path = os.path.join(project_path, "project.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            project_data = json.load(f)
                            project = Project.from_dict(project_data)
                            projects.append(project)
                    except Exception as e:
                        logger.error(f"Failed to load project from {config_path}: {str(e)}")
        
        return projects
    
    async def save(self, project: Project) -> str:
        """Save a project.
        
        If the project already exists, it will be updated.
        If the project does not exist, it will be created.
        
        Args:
            project: The project to save
            
        Returns:
            The ID of the saved project
        """
        project_dir = os.path.join(self.projects_dir, project.id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Ensure source code and docs directories exist
        os.makedirs(os.path.join(project_dir, project.source_code_dir), exist_ok=True)
        os.makedirs(os.path.join(project_dir, project.docs_dir), exist_ok=True)
        
        # Update the updated_at timestamp
        project.updated_at = datetime.now()
        
        # Save the project configuration
        config_path = os.path.join(project_dir, "project.json")
        with open(config_path, "w") as f:
            json.dump(project.to_dict(), f, indent=2)
        
        # Update todo.md
        await self._update_todo_markdown(project)
        
        logger.info(f"Saved project {project.name} (ID: {project.id})")
        
        return project.id
    
    async def delete(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        project_dir = os.path.join(self.projects_dir, project_id)
        
        if not os.path.exists(project_dir):
            return False
            
        try:
            shutil.rmtree(project_dir)
            logger.info(f"Deleted project with ID {project_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            return False
    
    async def find_by_name(self, name: str) -> List[Project]:
        """Find projects by name.
        
        Args:
            name: Name to search for
            
        Returns:
            List of projects matching the name
        """
        projects = await self.list_all()
        return [p for p in projects if name.lower() in p.name.lower()]
    
    async def find_by_tag(self, tag: str) -> List[Project]:
        """Find projects by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of projects with the specified tag
        """
        projects = await self.list_all()
        return [p for p in projects if tag in p.tags]
    
    async def _update_todo_markdown(self, project: Project) -> None:
        """Update the todo.md file for a project.
        
        Args:
            project: The project to update the todo.md for
        """
        todo_path = os.path.join(self.projects_dir, project.id, "todo.md")
        
        content = f"# {project.name} - Todo List\n\n"
        
        # Add project-level todos
        if project.todos:
            content += "## Project Todos\n\n"
            for todo in project.todos:
                status_marker = "- [x]" if todo.status == "DONE" else "- [ ]"
                content += f"{status_marker} **{todo.title}**"
                if todo.priority:
                    content += f" (Priority: {todo.priority})"
                content += "\n"
                if todo.description:
                    content += f"  - {todo.description}\n"
                if todo.assigned_to:
                    content += f"  - Assigned to: {todo.assigned_to}\n"
                content += "\n"
        
        # Add sprint todos
        for sprint in project.sprints:
            if sprint.todos:
                content += f"## Sprint: {sprint.name}\n\n"
                if sprint.description:
                    content += f"{sprint.description}\n\n"
                    
                content += f"Status: {sprint.status}\n\n"
                
                for todo in sprint.todos:
                    status_marker = "- [x]" if todo.status == "DONE" else "- [ ]"
                    content += f"{status_marker} **{todo.title}**"
                    if todo.priority:
                        content += f" (Priority: {todo.priority})"
                    content += "\n"
                    if todo.description:
                        content += f"  - {todo.description}\n"
                    if todo.assigned_to:
                        content += f"  - Assigned to: {todo.assigned_to}\n"
                    content += "\n"
        
        with open(todo_path, "w") as f:
            f.write(content)
