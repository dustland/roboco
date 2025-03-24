"""
Project Manager Module

This module provides functionality for managing projects, including their tasks
and associated teams and jobs.
"""

import os
import json
import uuid
import shutil
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import markdown
import time
import yaml
from datetime import timedelta

from loguru import logger

from roboco.core.schema import ProjectConfig, Task
from roboco.core import config


class ProjectManager:
    """Manager for projects and their components.
    
    This class provides methods for creating, updating, and retrieving projects,
    as well as managing tasks within projects.
    """
    
    def __init__(self, projects_dir: Optional[str] = None):
        """Initialize the project manager.
        
        Args:
            projects_dir: Optional custom directory for storing projects
        """
        self.config = config.load_config()
        self.projects_dir = projects_dir or os.path.join(self.config.core.workspace_base, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)
        self.projects: Dict[str, ProjectConfig] = {}
        self._load_projects()
    
    def _load_projects(self) -> None:
        """Load all existing projects from disk."""
        for project_dir in os.listdir(self.projects_dir):
            project_path = os.path.join(self.projects_dir, project_dir)
            if os.path.isdir(project_path):
                config_path = os.path.join(project_path, "project.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            project_data = json.load(f)
                            project_id = os.path.basename(project_dir)
                            self.projects[project_id] = ProjectConfig(**project_data)
                            logger.info(f"Loaded project: {project_data['name']} (ID: {project_id})")
                    except Exception as e:
                        logger.error(f"Failed to load project from {config_path}: {str(e)}")
    
    def _save_project(self, project_id: str) -> None:
        """Save a project to disk.
        
        Args:
            project_id: ID of the project to save
        """
        project = self.projects.get(project_id)
        if not project:
            logger.error(f"Cannot save project {project_id}: project not found")
            return
            
        project_dir = os.path.join(self.projects_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        
        # Ensure source code and docs directories exist
        os.makedirs(os.path.join(project_dir, project.source_code_dir), exist_ok=True)
        os.makedirs(os.path.join(project_dir, project.docs_dir), exist_ok=True)
        
        # Save the project configuration
        config_path = os.path.join(project_dir, "project.json")
        with open(config_path, "w") as f:
            json.dump(project.model_dump(), f, default=str, indent=2)
        
        # Update task.md
        self._update_task_markdown(project_id)
        
        logger.info(f"Saved project {project.name} (ID: {project_id})")
    
    def _update_task_markdown(self, project_id: str) -> None:
        """Update the task.md file for a project.
        
        Args:
            project_id: ID of the project to update
        """
        project = self.projects.get(project_id)
        if not project:
            return
            
        task_path = os.path.join(self.projects_dir, project_id, "task.md")
        
        content = f"# {project.name} - Task List\n\n"
        content += f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Add tasks section
        if project.tasks:
            # Group tasks by status
            todo_tasks = [t for t in project.tasks if t.status == "TODO"]
            in_progress_tasks = [t for t in project.tasks if t.status == "IN_PROGRESS"]
            done_tasks = [t for t in project.tasks if t.status == "DONE"]
            
            if in_progress_tasks:
                content += "## In Progress\n\n"
                for task in in_progress_tasks:
                    assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                    priority_marker = {"low": "🔽", "medium": "⏺️", "high": "🔼", "critical": "‼️"}.get(task.priority.lower(), "")
                    content += f"- [ ] {priority_marker} {task.title}{assigned} - {task.description or ''}\n"
                content += "\n"
            
            if todo_tasks:
                content += "## To Do\n\n"
                for task in todo_tasks:
                    assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                    priority_marker = {"low": "🔽", "medium": "⏺️", "high": "🔼", "critical": "‼️"}.get(task.priority.lower(), "")
                    content += f"- [ ] {priority_marker} {task.title}{assigned} - {task.description or ''}\n"
                content += "\n"
            
            if done_tasks:
                content += "## Completed\n\n"
                for task in done_tasks:
                    assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                    content += f"- [x] {task.title}{assigned} - {task.description or ''}\n"
                content += "\n"
        
        # Write the task.md file
        with open(task_path, "w") as f:
            f.write(content)
        
        logger.info(f"Updated task.md for project {project.name} (ID: {project_id})")
    
    def create_project(self, name: str, description: str, directory: Optional[str] = None,
                     teams: Optional[List[str]] = None, tags: Optional[List[str]] = None,
                     source_code_dir: str = "src", docs_dir: str = "docs") -> str:
        """Create a new project.
        
        Args:
            name: Name of the project
            description: Description of the project
            directory: Optional custom directory name (defaults to sanitized project name)
            teams: Optional list of team keys to associate with this project
            tags: Optional tags for the project
            source_code_dir: Directory for source code (relative to project directory)
            docs_dir: Directory for documentation (relative to project directory)
            
        Returns:
            The ID of the created project
        """
        # Generate a unique ID for the project
        project_id = str(uuid.uuid4())
        
        # Create a sanitized directory name if not provided
        if not directory:
            directory = name.lower().replace(" ", "_").replace("-", "_")
        
        # Create the project config
        project = ProjectConfig(
            name=name,
            description=description,
            directory=directory,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            teams=teams or [],
            tags=tags or [],
            source_code_dir=source_code_dir,
            docs_dir=docs_dir
        )
        
        # Save the project
        self.projects[project_id] = project
        self._save_project(project_id)
        
        return project_id
    
    def get_project(self, project_id: str) -> Optional[ProjectConfig]:
        """Get a project by ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            The project configuration or None if not found
        """
        return self.projects.get(project_id)
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects.
        
        Returns:
            List of project information dictionaries with id and summary data
        """
        return [
            {
                "id": project_id,
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at,
                "updated_at": project.updated_at,
                "teams": project.teams,
                "tags": project.tags,
                "jobs_count": len(project.jobs),
                "tasks_count": len(project.tasks)
            }
            for project_id, project in self.projects.items()
        ]
    
    def update_project(self, project_id: str, **updates) -> bool:
        """Update a project.
        
        Args:
            project_id: ID of the project to update
            **updates: Attributes to update
            
        Returns:
            True if the project was updated, False otherwise
        """
        project = self.projects.get(project_id)
        if not project:
            return False
        
        # Update fields
        for field, value in updates.items():
            if hasattr(project, field) and field != "created_at":
                setattr(project, field, value)
        
        # Update last updated timestamp
        project.updated_at = datetime.now()
        
        # Save changes
        self._save_project(project_id)
        
        return True
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project.
        
        Args:
            project_id: ID of the project to delete
            
        Returns:
            True if the project was deleted, False otherwise
        """
        if project_id not in self.projects:
            return False
        
        # Remove from projects dictionary
        project = self.projects.pop(project_id)
        
        # Delete from disk
        project_dir = os.path.join(self.projects_dir, project_id)
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        logger.info(f"Deleted project {project.name} (ID: {project_id})")
        
        return True
    
    def add_job_to_project(self, project_id: str, job_id: str) -> bool:
        """Add a job to a project.
        
        Args:
            project_id: ID of the project
            job_id: ID of the job to add
            
        Returns:
            True if the job was added, False otherwise
        """
        project = self.projects.get(project_id)
        if not project:
            return False
        
        if job_id not in project.jobs:
            project.jobs.append(job_id)
            project.updated_at = datetime.now()
            self._save_project(project_id)
        
        return True
    
    def create_task(self, project_id: str, title: str, description: Optional[str] = None,
                  status: str = "TODO", assigned_to: Optional[str] = None,
                  priority: str = "medium", depends_on: Optional[List[str]] = None,
                  tags: Optional[List[str]] = None) -> Optional[Task]:
        """Create a new task.
        
        Args:
            project_id: ID of the project
            title: Title of the task
            description: Optional description
            status: Status (TODO, IN_PROGRESS, DONE)
            assigned_to: Optional assignee
            priority: Priority level (low, medium, high, critical)
            depends_on: Optional list of task IDs this task depends on
            tags: Optional tags
            
        Returns:
            The created task or None if the project wasn't found
        """
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Create the task
        task = Task(
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to,
            priority=priority,
            depends_on=depends_on or [],
            tags=tags or []
        )
        
        # Add to project tasks
        project.tasks.append(task)
        
        # Update last updated timestamp
        project.updated_at = datetime.now()
        
        # Save changes
        self._save_project(project_id)
        
        return task
    
    def update_task(self, project_id: str, task_title: str, **updates) -> bool:
        """Update a task.
        
        Args:
            project_id: ID of the project
            task_title: Title of the task to update
            **updates: Attributes to update
            
        Returns:
            True if the task was updated, False otherwise
        """
        project = self.projects.get(project_id)
        if not project:
            return False
        
        # Check project tasks
        for i, task in enumerate(project.tasks):
            if task.title == task_title:
                for field, value in updates.items():
                    if hasattr(task, field):
                        setattr(task, field, value)
                
                task.updated_at = datetime.now()
                if updates.get("status") == "DONE" and not task.completed_at:
                    task.completed_at = datetime.now()
                
                project.updated_at = datetime.now()
                self._save_project(project_id)
                return True
        
        return False