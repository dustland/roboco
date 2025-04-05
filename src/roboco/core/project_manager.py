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
        return self.tasks
        
    def mark_task_completed(self, task: Task) -> bool:
        """
        Mark a specific task as completed in the database.
        
        Args:
            task: The task to mark as completed
            
        Returns:
            True if the task was marked as completed
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import update_task
        from roboco.core.models.task import TaskStatus
        
        # Update task status
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        
        # Update the task in the database
        updated_task = update_task(task.id, task)
        
        return True
    
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
            "id": self.project_id
        }
        execution_context = self._task_manager.generate_task_context(task, self.tasks, project_info)
        
        # Initialize results
        results = {"task": task.description, "status": "pending"}
        
        try:
            # Format task prompt
            task_prompt = f"""
Task: {task.description}

Details:
No additional details provided.

CONTEXT:
{execution_context}

Instructions:
- You have access to the filesystem tool for all file operations
- Use the filesystem tool to read and write files, create directories, etc.
- All file paths must be relative to the project root
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
        results["files"] = self.fs.list_sync(".")
        
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
        manifest: ProjectManifest = None,
        use_files: bool = True
    ) -> 'ProjectManager':
        """
        Initialize a new project both in database and optionally on disk.
        
        Args:
            name: Project name
            description: Project description
            project_id: Project ID
            directory: Optional directory path (defaults to project_id)
            manifest: ProjectManifest object
            use_files: Whether to create files on disk (defaults to True)
            
        Returns:
            ProjectManager instance for the newly created project
        """
        # Use project_id as directory if not specified
        if not directory:
            directory = project_id
            
        # Validate manifest is provided
        if manifest is None:
            raise ValueError("ProjectManifest is required for project initialization")
            
        # Validate manifest is the right type
        if not isinstance(manifest, ProjectManifest):
            raise TypeError("manifest must be a ProjectManifest object")
            
        # Use manifest's ID
        project_id = manifest.id
            
        # Validate file paths: Reject any paths with project ID prefixes
        invalid_paths = []
        for file_info in manifest.files:
            if file_info.path.startswith(f"{project_id}/") or file_info.path.startswith(f"{project_id}\\"):
                invalid_paths.append(file_info.path)
        
        # Also check folder paths
        for folder in manifest.folder_structure:
            if folder.startswith(f"{project_id}/") or folder.startswith(f"{project_id}\\"):
                invalid_paths.append(folder)
        
        # Fail fast if any invalid paths are found
        if invalid_paths:
            error_msg = f"Invalid file paths with project ID prefixes found: {', '.join(invalid_paths)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Create ProjectFS for the new project
        fs = ProjectFS(project_id=project_id)
        
        # Create metadata dictionary
        meta = {}
        if manifest.folder_structure:
            meta["folder_structure"] = manifest.folder_structure
        
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
            # Create directories
            for folder in manifest.folder_structure:
                fs.mkdir_sync(folder)
            
            # Create files
            for file_info in manifest.files:
                # Handle tasks.md file specially
                if file_info.path == "tasks.md":
                    # Save tasks.md file as provided
                    markdown_content = file_info.content
                    fs.write_sync(file_info.path, markdown_content)
                    
                    # Create task manager for task operations
                    task_manager = TaskManager(fs=fs)
                    
                    # Parse the markdown content into Task objects
                    task_objects = task_manager.parse_tasks_from_markdown(markdown_content, project_id)
                    
                    # Store tasks in database
                    from roboco.db.service import create_task
                    for task in task_objects:
                        create_task(project_id, task)
                else:
                    # Write file as is
                    fs.write_sync(file_info.path, file_info.content)
            
            # Write project.json
            project_json = project.to_dict()
            fs.write_sync("project.json", json.dumps(project_json, indent=2))
        
        # Create the project manager
        project_manager = cls(
            project=project,
            fs=fs,
            directory=directory
        )
        
        return project_manager
        
    def get_database_model(self) -> Project:
        """
        Get the Project model instance for database operations.
        
        Returns:
            A copy of the Project model instance
        """
        return self.project 