"""
Project Manager Module

This module provides functionality for managing projects, including their todos,
sprints, and associated teams and jobs.
"""

import os
import json
import uuid
import shutil
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path
import markdown

from loguru import logger

from roboco.core.schema import ProjectConfig, TodoItem, Sprint
from roboco.core import config


class ProjectManager:
    """Manager for projects and their components.
    
    This class provides methods for creating, updating, and retrieving projects,
    as well as managing todos and sprints within projects.
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
        
        # Update todo.md
        self._update_todo_markdown(project_id)
        
        logger.info(f"Saved project {project.name} (ID: {project_id})")
    
    def _update_todo_markdown(self, project_id: str) -> None:
        """Update the todo.md file for a project.
        
        Args:
            project_id: ID of the project to update
        """
        project = self.projects.get(project_id)
        if not project:
            return
            
        todo_path = os.path.join(self.projects_dir, project_id, "todo.md")
        
        content = f"# {project.name} - Todo List\n\n"
        content += f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
        
        # Add current sprint section if there is one
        active_sprint = project.get_active_sprint()
        if active_sprint:
            content += f"## Current Sprint: {active_sprint.name}\n\n"
            content += f"*{active_sprint.description}*\n\n" if active_sprint.description else "\n"
            content += f"**Duration:** {active_sprint.start_date.strftime('%Y-%m-%d')} to {active_sprint.end_date.strftime('%Y-%m-%d')}\n\n"
            
            if active_sprint.todos:
                content += "### Sprint Tasks\n\n"
                
                # Group tasks by status
                todo_tasks = [t for t in active_sprint.todos if t.status == "TODO"]
                in_progress_tasks = [t for t in active_sprint.todos if t.status == "IN_PROGRESS"]
                done_tasks = [t for t in active_sprint.todos if t.status == "DONE"]
                
                if in_progress_tasks:
                    content += "#### In Progress\n\n"
                    for task in in_progress_tasks:
                        assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                        priority_marker = {"low": "🔽", "medium": "⏺️", "high": "🔼", "critical": "‼️"}.get(task.priority.lower(), "")
                        content += f"- [ ] {priority_marker} {task.title}{assigned} - {task.description or ''}\n"
                    content += "\n"
                
                if todo_tasks:
                    content += "#### To Do\n\n"
                    for task in todo_tasks:
                        assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                        priority_marker = {"low": "🔽", "medium": "⏺️", "high": "🔼", "critical": "‼️"}.get(task.priority.lower(), "")
                        content += f"- [ ] {priority_marker} {task.title}{assigned} - {task.description or ''}\n"
                    content += "\n"
                
                if done_tasks:
                    content += "#### Completed\n\n"
                    for task in done_tasks:
                        assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                        content += f"- [x] {task.title}{assigned} - {task.description or ''}\n"
                    content += "\n"
        
        # Add backlog section with remaining todos
        if project.todos:
            content += "## Backlog\n\n"
            for task in project.todos:
                assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                priority_marker = {"low": "🔽", "medium": "⏺️", "high": "🔼", "critical": "‼️"}.get(task.priority.lower(), "")
                content += f"- [ ] {priority_marker} {task.title}{assigned} - {task.description or ''}\n"
        
        # Add future sprints section
        future_sprints = [s for s in project.sprints if s.name != project.current_sprint and s.status != "completed"]
        if future_sprints:
            content += "\n## Upcoming Sprints\n\n"
            for sprint in future_sprints:
                content += f"### {sprint.name}\n\n"
                content += f"*{sprint.description}*\n\n" if sprint.description else "\n"
                content += f"**Duration:** {sprint.start_date.strftime('%Y-%m-%d')} to {sprint.end_date.strftime('%Y-%m-%d')}\n\n"
                
                if sprint.todos:
                    content += "#### Planned Tasks\n\n"
                    for task in sprint.todos:
                        assigned = f" (@{task.assigned_to})" if task.assigned_to else ""
                        priority_marker = {"low": "🔽", "medium": "⏺️", "high": "🔼", "critical": "‼️"}.get(task.priority.lower(), "")
                        content += f"- [ ] {priority_marker} {task.title}{assigned} - {task.description or ''}\n"
                    content += "\n"
        
        # Write the todo.md file
        with open(todo_path, "w") as f:
            f.write(content)
        
        logger.info(f"Updated todo.md for project {project.name} (ID: {project_id})")
    
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
            teams=teams or [],
            tags=tags or [],
            source_code_dir=source_code_dir,
            docs_dir=docs_dir
        )
        
        # Add to projects dictionary
        self.projects[project_id] = project
        
        # Save to disk
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
                "sprints_count": len(project.sprints),
                "todos_count": len(project.todos) + sum(len(sprint.todos) for sprint in project.sprints)
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
    
    def create_todo(self, project_id: str, title: str, description: Optional[str] = None,
                  status: str = "TODO", assigned_to: Optional[str] = None,
                  priority: str = "medium", depends_on: Optional[List[str]] = None,
                  tags: Optional[List[str]] = None, sprint_name: Optional[str] = None) -> Optional[TodoItem]:
        """Create a new todo item.
        
        Args:
            project_id: ID of the project
            title: Title of the todo
            description: Optional description
            status: Status (TODO, IN_PROGRESS, DONE)
            assigned_to: Optional assignee
            priority: Priority level (low, medium, high, critical)
            depends_on: Optional list of task IDs this task depends on
            tags: Optional tags
            sprint_name: Optional sprint to assign the todo to
            
        Returns:
            The created todo item or None if the project wasn't found
        """
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Create the todo item
        todo = TodoItem(
            title=title,
            description=description,
            status=status,
            assigned_to=assigned_to,
            priority=priority,
            depends_on=depends_on or [],
            tags=tags or []
        )
        
        # Add to sprint or project todos
        if sprint_name:
            for sprint in project.sprints:
                if sprint.name == sprint_name:
                    sprint.todos.append(todo)
                    break
            else:
                # If sprint not found, add to project todos
                project.todos.append(todo)
        else:
            project.todos.append(todo)
        
        # Update last updated timestamp
        project.updated_at = datetime.now()
        
        # Save changes
        self._save_project(project_id)
        
        return todo
    
    def update_todo(self, project_id: str, todo_title: str, **updates) -> bool:
        """Update a todo item.
        
        Args:
            project_id: ID of the project
            todo_title: Title of the todo to update
            **updates: Attributes to update
            
        Returns:
            True if the todo was updated, False otherwise
        """
        project = self.projects.get(project_id)
        if not project:
            return False
        
        # Check project todos
        for i, todo in enumerate(project.todos):
            if todo.title == todo_title:
                for field, value in updates.items():
                    if hasattr(todo, field):
                        setattr(todo, field, value)
                
                # Handle moving to a sprint
                if "sprint_name" in updates and updates["sprint_name"]:
                    sprint_name = updates["sprint_name"]
                    for sprint in project.sprints:
                        if sprint.name == sprint_name:
                            sprint.todos.append(todo)
                            project.todos.pop(i)
                            break
                
                todo.updated_at = datetime.now()
                if updates.get("status") == "DONE" and not todo.completed_at:
                    todo.completed_at = datetime.now()
                
                project.updated_at = datetime.now()
                self._save_project(project_id)
                return True
        
        # Check sprint todos
        for sprint in project.sprints:
            for i, todo in enumerate(sprint.todos):
                if todo.title == todo_title:
                    for field, value in updates.items():
                        if hasattr(todo, field):
                            setattr(todo, field, value)
                    
                    # Handle moving to another sprint or back to backlog
                    if "sprint_name" in updates:
                        if not updates["sprint_name"]:
                            # Move to backlog
                            project.todos.append(todo)
                            sprint.todos.pop(i)
                        elif updates["sprint_name"] != sprint.name:
                            # Move to another sprint
                            for other_sprint in project.sprints:
                                if other_sprint.name == updates["sprint_name"]:
                                    other_sprint.todos.append(todo)
                                    sprint.todos.pop(i)
                                    break
                    
                    todo.updated_at = datetime.now()
                    if updates.get("status") == "DONE" and not todo.completed_at:
                        todo.completed_at = datetime.now()
                    
                    project.updated_at = datetime.now()
                    self._save_project(project_id)
                    return True
        
        return False
    
    def create_sprint(self, project_id: str, name: str, description: Optional[str] = None,
                    start_date: Optional[datetime] = None, end_date: Optional[datetime] = None,
                    status: str = "planned") -> Optional[Sprint]:
        """Create a new sprint.
        
        Args:
            project_id: ID of the project
            name: Name of the sprint
            description: Optional description
            start_date: Start date (defaults to tomorrow)
            end_date: End date (defaults to 2 weeks from start)
            status: Status (planned, active, completed)
            
        Returns:
            The created sprint or None if the project wasn't found
        """
        project = self.projects.get(project_id)
        if not project:
            return None
        
        # Set default dates if not provided
        if not start_date:
            from datetime import timedelta
            start_date = datetime.now() + timedelta(days=1)
            
        if not end_date:
            from datetime import timedelta
            end_date = start_date + timedelta(days=14)
        
        # Create the sprint
        sprint = Sprint(
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            status=status,
            todos=[]
        )
        
        # Add to project sprints
        project.sprints.append(sprint)
        
        # Set as current sprint if active and no current sprint
        if status == "active" and not project.current_sprint:
            project.current_sprint = name
        
        # Update last updated timestamp
        project.updated_at = datetime.now()
        
        # Save changes
        self._save_project(project_id)
        
        return sprint
    
    def update_sprint(self, project_id: str, sprint_name: str, **updates) -> bool:
        """Update a sprint.
        
        Args:
            project_id: ID of the project
            sprint_name: Name of the sprint to update
            **updates: Attributes to update
            
        Returns:
            True if the sprint was updated, False otherwise
        """
        project = self.projects.get(project_id)
        if not project:
            return False
        
        for sprint in project.sprints:
            if sprint.name == sprint_name:
                for field, value in updates.items():
                    if hasattr(sprint, field):
                        setattr(sprint, field, value)
                
                # If status changed to active, set as current sprint
                if updates.get("status") == "active":
                    project.current_sprint = sprint.name
                # If status changed to completed and this was the current sprint, unset current sprint
                elif updates.get("status") == "completed" and project.current_sprint == sprint.name:
                    project.current_sprint = None
                
                project.updated_at = datetime.now()
                self._save_project(project_id)
                return True
        
        return False 