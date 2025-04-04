"""
Project Manager

This module defines the ProjectManager entity with data management functionality.
It incorporates project data, loading/saving, and task execution.
"""

import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import traceback
from sqlmodel import Session, create_engine

from roboco.core.models.task import Task, TaskStatus
from roboco.core.models.project import Project
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.core.fs import ProjectFS, ProjectNotFoundError
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
        directory: Optional[str] = None,
    ):
        """
        Initialize a project manager.
        
        Args:
            project: Project model instance
            fs: ProjectFS instance for file operations
            directory: Directory path for the project (defaults to project.id)
        """
        # Store the Project model instance
        self.project = project
        
        # Use project.id as directory if not specified
        self.directory = directory or project.id
            
        # Initialize file system
        self.fs = fs
        
        # Store tasks as Task objects
        self.tasks = []
        
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
        """Get the project ID (same as directory name)."""
        return self.project.id
    
    @property
    def created_at(self) -> str:
        """Get the project creation time."""
        return self.project.created_at.isoformat() if self.project.created_at else None
    
    @property
    def updated_at(self) -> str:
        """Get the project update time."""
        return self.project.updated_at.isoformat() if self.project.updated_at else None
    
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
        
        # Add additional manager-specific fields
        result["directory"] = self.directory
        
        # Include tasks if loaded
        if self.tasks:
            result["tasks"] = [task.to_dict() if hasattr(task, 'to_dict') else task for task in self.tasks]
        
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
            directory=project.meta.get("directory", project.id)
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
        
        # Get directory or use project_id as fallback
        directory = data.get("directory", project.id)
        
        # Create the project manager
        project_manager = cls(
            project=project,
            fs=fs,
            directory=directory
        )
        
        # Add tasks if present
        tasks = []
        for task_data in data.get("tasks", []):
            if isinstance(task_data, dict):
                tasks.append(Task(**task_data))
            else:
                tasks.append(task_data)
        project_manager.tasks = tasks
        
        return project_manager
    
    def save(self) -> None:
        """
        Save the project to the database and optionally to project.json.
        
        This method updates the project in the database and also writes
        to project.json as a reference file (but never for loading back).
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import update_project
        from roboco.api.models.project import ProjectUpdate
        
        # Always update the timestamp before saving
        self.project.update_timestamp()
        
        # Create update data
        project_data = ProjectUpdate(
            name=self.project.name,
            description=self.project.description,
            meta=self.project.meta
        )
        
        # Update the project in the database
        try:
            updated_project = update_project(self.project.id, project_data)
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
            project_id: ID of the project
            
        Returns:
            ProjectManager instance
            
        Raises:
            ProjectNotFoundError: If the project does not exist in the database
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import get_project
        
        # Get project from database
        project = get_project(project_id)
        
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found in database")
        
        # Create file system for operations (even if we don't load from it)
        fs = ProjectFS(project_id=project_id)
        
        # Create and return the project manager
        return cls(
            project=project,
            fs=fs,
            directory=project_id
        )
    
    def load_tasks(self) -> List[Task]:
        """
        Load tasks from the database.
        
        Returns:
            List of Task objects
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import get_tasks_by_project
        
        # Get tasks from database
        self.tasks = get_tasks_by_project(self.project.id)
        
        # If no tasks found, check if there's a tasks.md file to load as a fallback
        if not self.tasks and self.fs.exists_sync("tasks.md"):
            logger.info(f"No tasks found in database for project {self.project.id}, loading from tasks.md as fallback")
            tasks_from_file = self._task_manager.load_tasks()
            
            # Save tasks to database for future reference
            if tasks_from_file:
                logger.info(f"Saving {len(tasks_from_file)} tasks from tasks.md to database")
                from roboco.api.models.task import TaskCreate
                from roboco.db.service import create_task
                
                for task in tasks_from_file:
                    # Create task data
                    task_data = TaskCreate(
                        title=task.description if hasattr(task, 'description') else "Untitled Task",
                        description=task.details[0] if hasattr(task, 'details') and task.details else None,
                        status=task.status,
                        meta={"details": task.details if hasattr(task, 'details') else []}
                    )
                    
                    # Create task in database
                    create_task(self.project.id, task_data)
                
                # Reload tasks from database to get properly linked tasks
                self.tasks = get_tasks_by_project(self.project.id)
        
        return self.tasks
        
    def mark_task_completed(self, task: Task) -> bool:
        """
        Mark a specific task as completed in the database and optionally in tasks.md.
        
        Args:
            task: The task to mark as completed
            
        Returns:
            True if the task was successfully marked, False otherwise
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import update_task
        from roboco.api.models.task import TaskUpdate
        from roboco.core.models.task import TaskStatus
        
        # Update task status in database
        try:
            # Create update data
            task_data = TaskUpdate(
                status=TaskStatus.COMPLETED
            )
            
            # Update the task in the database
            updated_task = update_task(task.id, task_data)
            
            if not updated_task:
                logger.error(f"Failed to update task {task.id} in database")
                return False
                
            # Also update tasks.md for reference (but never for loading back)
            self._task_manager.mark_task_completed(task)
            
            return True
        except Exception as e:
            logger.error(f"Error marking task {task.id} as completed: {str(e)}")
            return False
    
    def _convert_to_dict(self, obj):
        """
        Convert a potentially non-serializable object to a dictionary.
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation that's JSON serializable
        """
        if obj is None:
            return None
            
        # If it's already a dict, just process each value recursively
        if isinstance(obj, dict):
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
            
        # If it's a list, convert each item
        if isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
            
        # For objects with a to_dict method, use that
        if hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return self._convert_to_dict(obj.to_dict())
            
        # For objects with __dict__, convert to dictionary
        if hasattr(obj, '__dict__'):
            return {k: self._convert_to_dict(v) for k, v in obj.__dict__.items() 
                   if not k.startswith('_')}
            
        # Try to serialize, otherwise convert to string
        try:
            import json
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            return str(obj)
    
    def _create_batch_task_header(self, num_tasks: int) -> str:
        """
        Create a visually distinct header for a batch of tasks.
        
        Args:
            num_tasks: Number of tasks to be executed
            
        Returns:
            A formatted header string
        """
        separator = "*" * 80
        title = f" BEGINNING EXECUTION OF {num_tasks} TASKS "
        
        # Center the title within the separator
        centered_title = title.center(80, "*")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
        
    def _create_batch_completion_header(self, status: str, completed: int, total: int) -> str:
        """
        Create a visually distinct header for batch task completion.
        
        Args:
            status: Overall status of the batch
            completed: Number of successfully completed tasks
            total: Total number of tasks
            
        Returns:
            A formatted completion header string
        """
        separator = "*" * 80
        status_symbol = "✅" if status == "success" else "⚠️" if status == "partial_failure" else "❌"
        title = f" {status_symbol} TASK BATCH COMPLETE: {completed}/{total} tasks completed successfully [{status.upper()}] "
        
        # Center the title within the separator
        centered_title = title.center(80, "*")
        
        header = f"\n{separator}\n{centered_title}\n{separator}\n"
        return header
    
    async def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task.
        
        Args:
            task: Task to execute
            
        Returns:
            Results of task execution
        """
        # Skip already completed tasks
        if task.status == TaskStatus.COMPLETED:
            logger.info(f"Task '{task.description}' is already marked as completed, skipping execution")
            return {
                "task": task.description,
                "status": "already_completed"
            }
        
        # Log task execution
        task_header = self._task_manager.create_task_header(task)
        logger.info(task_header)
        logger.info(f"Executing task: {task.description}")
        
        # Get team for this task
        team = self.team_manager.get_team_for_task(task)
        
        # Get context for task execution
        project_info = {
            "name": self.name,
            "description": self.description,
            "id": self.project_id,
            "source_code_dir": self.source_code_dir,
            "docs_dir": self.docs_dir
        }
        execution_context = self._task_manager.generate_task_context(task, self.tasks, project_info)
        
        # Initialize results
        results = {"task": task.description, "status": "pending"}
        
        try:
            # Format task prompt
            task_prompt = f"""
Task: {task.description}

Details:
{chr(10).join([f"* {detail}" for detail in task.details]) if hasattr(task, 'details') and task.details else "No additional details provided."}

CONTEXT:
{execution_context}

Instructions:
- You have access to the filesystem tool for all file operations
- Use the filesystem tool to read and write files, create directories, etc.
- All file paths must be relative to the project root
- Place source code in the src directory
- Place documentation in the docs directory
- Maintain a clean, organized directory structure
"""
            
            # Execute task
            task_result = await team.run_chat(query=task_prompt)
            task_result = self._convert_to_dict(task_result)
            
            # Process result
            if "error" not in task_result:
                # Mark task as completed
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                self.mark_task_completed(task)
                
                results.update({
                    "status": "completed",
                    "response": task_result.get("response", "")
                })
                logger.info(f"Task '{task.description}' completed successfully")
            else:
                results.update({
                    "status": "failed",
                    "error": task_result.get("error", "Unknown error")
                })
                logger.error(f"Task '{task.description}' failed: {task_result.get('error')}")
            
        except Exception as e:
            results.update({
                "status": "failed",
                "error": str(e),
                "error_details": traceback.format_exc()
            })
            logger.error(f"Error executing task '{task.description}': {e}")
        
        # Log completion
        completion_header = self._task_manager.create_task_completion_header(task, results["status"])
        logger.info(completion_header)
        
        return results

    async def execute_tasks(self, keyword_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute all tasks in the project, optionally filtered by a keyword.
        Stops execution if any task fails.
        
        Args:
            keyword_filter: Optional keyword to filter tasks by description
            
        Returns:
            Dictionary containing execution results
        """
        # Make sure tasks are loaded
        if not self.tasks:
            self.load_tasks()
        
        if not self.tasks:
            return {"error": "No tasks found in the project", "status": "failed"}
        
        logger.info(f"Found {len(self.tasks)} tasks in project")
        
        # Filter tasks if needed
        tasks_to_execute = self.tasks
        if keyword_filter:
            filtered_tasks = [t for t in self.tasks if keyword_filter.lower() in t.description.lower()]
            if not filtered_tasks:
                return {"error": f"No tasks matching '{keyword_filter}' found", "status": "failed"}
            tasks_to_execute = filtered_tasks
            logger.info(f"Filtered to {len(tasks_to_execute)} tasks")
        
        # Track results
        results = {
            "tasks": {},
            "status": "success",
            "completed_count": 0
        }
        
        # Execute each task
        for task in tasks_to_execute:
            task_result = await self.execute_task(task)
            results["tasks"][task.description] = self._convert_to_dict(task_result)
            
            # Check task completion status
            if task_result["status"] in ["completed", "already_completed"]:
                results["completed_count"] += 1
            else:
                # Task failed, stop execution
                results["status"] = "failed"
                logger.error(f"Task '{task.description}' failed. Stopping further execution.")
                break
        
        # Add file summary
        results["files"] = {
            self.source_code_dir: self.fs.list_sync(self.source_code_dir),
            self.docs_dir: self.fs.list_sync(self.docs_dir)
        }
        
        # Update project timestamp and save
        self.project.update_timestamp()
        self.save()
        
        logger.info(f"Project tasks execution: {results['completed_count']}/{len(tasks_to_execute)} completed")
        return results
        
    @classmethod
    def initialize(
        cls,
        name: str,
        description: str,
        project_id: str,
        directory: Optional[str] = None,
        manifest: Optional[ProjectManifest] = None,
    ) -> 'ProjectManager':
        """
        Initialize a new project on disk.
        
        This method creates a project structure with appropriate
        directories and files. It processes the project manifest,
        creates the necessary file structure, and returns a ProjectManager instance.
        
        Args:
            name: Project name
            description: Project description
            project_id: Optional project ID
            directory: Optional directory path (defaults to project_id)
            manifest: Optional project manifest
            
        Returns:
            ProjectManager instance for the newly created project
        """
        # Use project_id as directory if not specified
        if not directory:
            directory = project_id
        
        # If manifest is provided and is a dictionary, convert it to a ProjectManifest
        if manifest:
            if isinstance(manifest, dict):
                manifest = dict_to_project_manifest(manifest)
        else:
            # Create a default manifest if none provided
            manifest = ProjectManifest(id=project_id)
        
        # Use manifest's ID if available, otherwise use the provided project_id
        project_id = manifest.id if manifest.id else project_id
        logger.debug(f"Using project_id: {project_id}")
        
        # Create ProjectFS for the new project
        fs = ProjectFS(project_id=project_id)
        
        # Create the Project model instance
        project = Project(
            id=project_id,
            name=name,
            description=description,
            meta=manifest.meta or {}
        )
        
        # Store folder structure in metadata
        project.meta["folder_structure"] = manifest.folder_structure or ["src", "docs"]
        
        # Create custom structure if provided
        if manifest.folder_structure:
            # Create any additional directories
            for folder in manifest.folder_structure:
                # Ensure folder path is relative to project root
                folder_path = folder
                if folder_path.startswith(f"{project_id}/") or folder_path.startswith(f"{project_id}\\"):
                    folder_path = folder_path[len(project_id)+1:]  # +1 for the slash
                
                fs.mkdir_sync(folder_path)
                logger.debug(f"Created directory: {folder_path}")
                
            # Create any specified files
            if manifest.files:
                for file_info in manifest.files:
                    # Make path relative to project directory by removing project directory prefix if present
                    file_path = file_info.path
                    
                    # If the path starts with the project directory name, remove it
                    if file_path.startswith(f"{project_id}/") or file_path.startswith(f"{project_id}\\"):
                        relative_path = file_path[len(project_id)+1:]  # +1 for the slash
                    elif file_path == project_id:
                        relative_path = ""
                    else:
                        relative_path = file_path
                    
                    # Write file with the adjusted path
                    fs.write_sync(relative_path, file_info.content)
                    logger.debug(f"Created file: {relative_path}")
        
        # Create the project manager
        project_manager = cls(
            project=project,
            fs=fs,
            directory=directory
        )
        
        # Save the project to ensure it's persisted
        project_manager.save()
        
        logger.info(f"Created project '{name}' in directory: {project_id}")
        return project_manager

    @classmethod
    def initialize(
        cls,
        name: str,
        description: str,
        project_id: str,
        directory: Optional[str] = None,
        manifest: Optional[ProjectManifest] = None,
        use_files: bool = True
    ) -> 'ProjectManager':
        """
        Initialize a new project both in database and optionally on disk.
        
        This method creates a project in the database and optionally
        creates the file structure based on the manifest.
        
        Args:
            name: Project name
            description: Project description
            project_id: Project ID
            directory: Optional directory path (defaults to project_id)
            manifest: Optional project manifest
            use_files: Whether to create files on disk (defaults to True)
            
        Returns:
            ProjectManager instance for the newly created project
        """
        # Use project_id as directory if not specified
        if not directory:
            directory = project_id
        
        # If manifest is provided and is a dictionary, convert it to a ProjectManifest
        if manifest:
            if isinstance(manifest, dict):
                manifest = dict_to_project_manifest(manifest)
        else:
            # Create a default manifest if none provided
            manifest = ProjectManifest(id=project_id)
        
        # Use manifest's ID if available, otherwise use the provided project_id
        project_id = manifest.id if manifest.id and manifest.id != "None" else project_id
        logger.debug(f"Using project_id: {project_id}")
        
        # Create ProjectFS for the new project
        fs = ProjectFS(project_id=project_id)
        
        # Create meta dictionary from manifest
        meta = manifest.meta or {}
        meta["folder_structure"] = manifest.folder_structure or ["src", "docs"]
        
        # Import db operations here to avoid circular imports
        from roboco.api.models.project import ProjectCreate
        from roboco.db.service import create_project
        
        # Create project in database
        project_data = ProjectCreate(
            name=name,
            description=description,
            meta=meta
        )
        
        # Create the Project model instance in database with specific ID
        project = project_data.to_db_model()
        project.id = project_id  # Ensure ID is set correctly
        
        # Use database service to persist
        from roboco.db import get_session_context
        with get_session_context() as session:
            session.add(project)
            session.commit()
            session.refresh(project)
        
        # Create file structure if requested
        if use_files:
            # Create directory structure
            for folder in meta.get("folder_structure", ["src", "docs"]):
                # Ensure folder path is relative to project root
                folder_path = folder
                if folder_path.startswith(f"{project_id}/") or folder_path.startswith(f"{project_id}\\"):
                    folder_path = folder_path[len(project_id)+1:]  # +1 for the slash
                
                fs.mkdir_sync(folder_path)
                logger.debug(f"Created directory: {folder_path}")
            
            # Create specified files
            if manifest.files:
                for file_info in manifest.files:
                    # Make path relative to project directory
                    file_path = file_info.path
                    
                    # If the path starts with the project directory name, remove it
                    if file_path.startswith(f"{project_id}/") or file_path.startswith(f"{project_id}\\"):
                        relative_path = file_path[len(project_id)+1:]  # +1 for the slash
                    elif file_path == project_id:
                        relative_path = ""
                    else:
                        relative_path = file_path
                    
                    # Write file with the adjusted path
                    fs.write_sync(relative_path, file_info.content)
                    logger.debug(f"Created file: {relative_path}")
            
            # Write project.json for reference (but never for loading back)
            project_json = project.to_dict()
            fs.write_sync("project.json", json.dumps(project_json, indent=2))
            logger.debug(f"Created project.json for reference")
        
        # Create the project manager
        project_manager = cls(
            project=project,
            fs=fs,
            directory=directory
        )
        
        logger.info(f"Created project '{name}' with ID: {project_id}")
        return project_manager
        
    def get_database_model(self) -> Project:
        """
        Get the Project model instance for database operations.
        
        Returns:
            A copy of the Project model instance
        """
        return self.project 