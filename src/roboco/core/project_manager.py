"""
Project Manager

This module defines the ProjectManager entity with data management functionality.
It incorporates project data, loading/saving, and task execution.
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import traceback

from roboco.core.models.task import Task, TaskStatus
from roboco.core.models.project import Project
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.core.fs import ProjectFS
from roboco.core.team_manager import TeamManager
from roboco.core.task_manager import TaskManager
from roboco.utils.id_generator import generate_short_id


class ProjectManager:
    """
    Project management entity with data management capabilities.
    
    This class represents a project manager that utilizes the Project model for persistence
    while providing additional functionality for task execution and file management.
    """
    
    def __init__(
        self,
        project: Project,
        fs: ProjectFS,
    ):
        """
        Initialize a project manager.
        
        Args:
            project: Project model instance
            fs: ProjectFS instance for file operations
        """
        # Store the Project model instance
        self.project = project
        
        # Initialize file system
        self.fs = fs
        
        # Initialize team manager for task execution
        self._team_manager = TeamManager(self.fs)
        
        # Initialize task manager for task operations 
        self._task_manager = TaskManager(self.fs)
    
    # Property accessors that delegate to the Project model
    @property
    def id(self) -> str:
        """Get the project ID."""
        return self.project.id
    
    @property
    def name(self) -> str:
        """Get the project name."""
        return self.project.name
    
    @name.setter
    def name(self, value: str):
        """Set the project name and update timestamp."""
        self.project.name = value
        self.project.update_timestamp()
        self._sync_project()
    
    @property
    def description(self) -> str:
        """Get the project description."""
        return self.project.description
    
    @description.setter
    def description(self, value: str):
        """Set the project description and update timestamp."""
        self.project.description = value
        self.project.update_timestamp()
        self._sync_project()
    
    @property
    def project_id(self) -> str:
        """Get the project ID (alias for id)."""
        return self.project.id
    
    @property
    def created_at(self) -> datetime:
        """Get the project creation timestamp."""
        return self.project.created_at
    
    @property
    def updated_at(self) -> datetime:
        """Get the project update timestamp."""
        return self.project.updated_at
    
    @property
    def source_code_dir(self) -> str:
        """Get the source code directory."""
        return self.project.meta.get("source_code_dir", "src")
    
    @property
    def docs_dir(self) -> str:
        """Get the documentation directory."""
        return self.project.meta.get("docs_dir", "docs")
    
    @property
    def team_manager(self) -> TeamManager:
        """Get the team manager instance."""
        return self._team_manager
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update a metadata value in the project.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.project.meta[key] = value
        self.project.update_timestamp()
        self._sync_project()
    
    def _sync_project(self) -> None:
        """
        Sync the project model with the filesystem.
        This ensures changes are persisted immediately.
        """
        self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project to a dictionary.
        
        Returns:
            Dictionary representation of the project
        """
        # Start with the project model's dictionary
        result = self.project.to_dict()
        
        # Include tasks if needed by getting them directly from the task manager
        tasks = self._task_manager.load_tasks(self.project.id)
        if tasks:
            result["tasks"] = [task.to_dict() if hasattr(task, 'to_dict') else task for task in tasks]
        
        return result
    
    @classmethod
    def from_project_model(cls, project: Project, fs: Optional[ProjectFS] = None) -> 'ProjectManager':
        """
        Create a ProjectManager from a Project model instance.
        
        Args:
            project: Project model instance
            fs: Optional ProjectFS instance for file operations
            
        Returns:
            ProjectManager instance
        """
        # Create ProjectFS if not provided
        if not fs:
            fs = ProjectFS(project_id=project.id)
        
        # Create and return the project manager
        return cls(
            project=project,
            fs=fs,
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], fs: Optional[ProjectFS] = None) -> 'ProjectManager':
        """
        Create a project manager from a dictionary.
        
        Args:
            data: Dictionary representation of the project
            fs: Optional ProjectFS instance for file operations
            
        Returns:
            ProjectManager instance
        """
        # Extract Project model fields
        project_data = {
            "id": data.get("id", generate_short_id()),
            "name": data.get("name", "Untitled Project"),
            "description": data.get("description"),
            "meta": data.get("meta", {}) or {},  # Handle None
        }
        
        # Handle timestamps
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            try:
                project_data["created_at"] = datetime.fromisoformat(created_at)
            except ValueError:
                # Default to current time if parsing fails
                project_data["created_at"] = datetime.utcnow()
        
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            try:
                project_data["updated_at"] = datetime.fromisoformat(updated_at)
            except ValueError:
                # Default to current time if parsing fails
                project_data["updated_at"] = datetime.utcnow()
        
        # Ensure metadata is a dict
        if not project_data["meta"]:
            project_data["meta"] = {}
        
        # Create Project model instance
        project = Project(**project_data)
        
        # Create ProjectFS if not provided
        if not fs and project.id:
            fs = ProjectFS(project_id=project.id)
        
        # Create the project manager
        project_manager = cls(
            project=project,
            fs=fs
        )
        
        # Handle tasks if present in the data
        task_data_list = data.get("tasks", [])
        if task_data_list:
            # Create TaskManager to handle task creation
            task_manager = TaskManager(fs)
            
            # Process each task
            for task_data in task_data_list:
                if isinstance(task_data, dict):
                    # Extract task fields
                    title = task_data.get("title", "Untitled Task")
                    description = task_data.get("description", "")
                    status_str = task_data.get("status", "todo")
                    
                    # Map string status to TaskStatus enum
                    from roboco.core.models.task import TaskStatus
                    status = TaskStatus.TODO
                    if status_str == "completed":
                        status = TaskStatus.COMPLETED
                    elif status_str == "in_progress":
                        status = TaskStatus.IN_PROGRESS
                    elif status_str == "blocked":
                        status = TaskStatus.BLOCKED
                    elif status_str == "canceled":
                        status = TaskStatus.CANCELED
                    elif status_str == "failed":
                        status = TaskStatus.FAILED
                    
                    # Extract details
                    details = task_data.get("details", [])
                    
                    # Create the task using TaskManager
                    task_manager.create_task(
                        title=title,
                        description=description,
                        project_id=project.id,
                        status=status,
                        details=details
                    )
        
        return project_manager
    
    def save(self) -> None:
        """
        Save the project to the database and optionally to project.json.
        
        This method updates the project in the database and also writes
        to project.json as a reference file (but never for loading back).
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import update_project
        
        # Always update the timestamp before saving
        self.project.update_timestamp()
        
        # Update the project in the database using direct domain model
        # No API model dependencies - use domain model directly
        try:
            updated_project = update_project(self.project.id, self.project)
            if not updated_project:
                logger.error(f"Failed to update project {self.project.id} in database")
        except Exception as e:
            logger.error(f"Error updating project {self.project.id} in database: {str(e)}")
        
        # Also save to project.json for reference (but never for loading back)
        try:
            # Convert to dictionary
            project_data_dict = self.to_dict()
            
            # Write to project.json
            json_content = json.dumps(project_data_dict, indent=2)
            self.fs.write_sync("project.json", json_content)
            
            logger.info(f"Saved project {self.id} to database and {self.project_id}/project.json")
        except Exception as e:
            logger.error(f"Error writing project.json for {self.project.id}: {str(e)}")
    
    @classmethod
    def load(cls, project_id: str) -> 'ProjectManager':
        """
        Load a project from the database.
        
        Args:
            project_id: ID of the project to load
            
        Returns:
            ProjectManager instance
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import get_project
        
        # Get project from database
        project = get_project(project_id)
        
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Create and return project manager
        return cls(
            project=project,
            fs=fs
        )
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task by delegating to TaskManager.
        
        Args:
            task: Task to execute
            
        Returns:
            Results of task execution
        """
        # Get all project tasks for context directly from the task manager
        all_tasks = self._task_manager.load_tasks(self.project.id)
            
        # Get project info for context generation
        project_info = {
            "name": self.name,
            "description": self.description,
            "id": self.project_id
        }
        
        # Delegate to TaskManager for execution
        return await self._task_manager.execute_task(task, all_tasks)
    
    async def execute(self) -> Dict[str, Any]:
        """
        Execute the project by running all its tasks.
        
        Returns:
            Dictionary containing execution results
        """
        # Load tasks directly from the task manager
        tasks = self._task_manager.load_tasks(self.project.id)
        
        if not tasks:
            return {"error": "No tasks found in the project", "status": "failed"}
        
        logger.info(f"Found {len(tasks)} tasks in project")
        
        # Delegate to TaskManager for execution
        results = await self._task_manager.execute_tasks(tasks)
        
        # Add file summary
        results["files"] = self.fs.list_sync(".")
        
        # Update project timestamp and save
        self.project.update_timestamp()
        self.save()
        
        # Log summary
        completed_count = sum(1 for task_result in results["tasks"].values() 
                             if task_result.get("status") in ["completed", "already_completed"])
        logger.info(f"Project tasks execution: {completed_count}/{len(tasks)} completed")
        
        return results
    
    def _convert_to_dict(self, obj):
        """
        Convert a potentially non-serializable object to a dictionary.
        
        Args:
            obj: The object to convert
            
        Returns:
            A dictionary representing the object
        """
        # If object has a to_dict method, use it
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        
        # If object has a dict method (like Pydantic models), use it
        if hasattr(obj, 'dict'):
            return obj.dict()
            
        # If object is already a dict, return it
        if isinstance(obj, dict):
            return obj
            
        # Otherwise convert to a dictionary using vars()
        return vars(obj)
    
    @classmethod
    def initialize(cls, name: str, description: str, 
                project_id: Optional[str] = None, 
                manifest: Optional[ProjectManifest] = None,
                use_files: bool = True) -> 'ProjectManager':
        """
        Initialize a new project with the given parameters.
        
        Args:
            name: Name of the project
            description: Description of the project 
            project_id: Optional project ID to use (generated if not provided)
            manifest: Optional project manifest to use for initialization
            use_files: Whether to create the file structure (default: True)
            
        Returns:
            ProjectManager instance
        """
        from roboco.core.models.project import Project
        import json
        
        # Generate project ID or use the provided one
        if project_id is None:
            project_id = generate_short_id()
            logger.info(f"Generated project ID: {project_id}")
            
        # Use manifest's ID if provided
        if manifest:
            project_id = manifest.id
        
        # Create ProjectFS for the new project
        fs = ProjectFS(project_id=project_id)
        
        # Create metadata dictionary
        meta = {}
        # Default folder structure for every project
        meta["folder_structure"] = ["src", "docs", "tests"]
        
        # Create the Project model instance
        project = Project(
            id=project_id,
            name=name,
            description=description,
            meta=meta
        )
        
        # Save to database
        from roboco.db import get_session_context
        
        try:
            with get_session_context() as session:
                session.add(project)
                session.commit()
                session.refresh(project)
        except Exception as e:
            # If a project with this ID already exists, this is likely a race condition
            # Let the error propagate as we should fail fast
            logger.error(f"Error creating project in database: {str(e)}")
            raise  # Re-raise the exception to be handled by the caller
        
        # Create file structure if requested
        if use_files:
            # Create standard directories
            for folder in meta["folder_structure"]:
                fs.mkdir_sync(folder)
            
            # Write project.json
            project_json = project.to_dict()
            fs.write_sync("project.json", json.dumps(project_json, indent=2))
        
        # Create the project manager
        project_manager = cls(
            project=project,
            fs=fs
        )
        
        # Generate and create tasks if we have tasks in the manifest
        if manifest and manifest.tasks:
            # Create a task manager
            task_manager = TaskManager(fs)
            
            # Generate tasks.md content
            tasks_md_content = manifest.tasks_to_markdown()
            fs.write_sync("tasks.md", tasks_md_content)
            
            # Let the TaskManager handle task creation
            for task_data in manifest.tasks:
                task_manager.create_task(
                    title=task_data.title,
                    description=task_data.description,
                    project_id=project_id,
                    status=TaskStatus.TODO if task_data.status == "todo" else TaskStatus.COMPLETED,
                    details=task_data.details
                )
        
        return project_manager
        
    def get_database_model(self) -> Project:
        """
        Get the Project model instance for database operations.
        
        Returns:
            A copy of the Project model instance
        """
        return self.project 