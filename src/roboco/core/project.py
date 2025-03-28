"""
Project Domain Model

This module defines the Project domain entity with data management functionality.
It incorporates project data, loading/saving, and task execution.
"""

import json
import re
from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
import traceback

from roboco.core.models.task import Task, TaskStatus
from roboco.core.models.project_metadata import ProjectMetadata
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.core.project_fs import ProjectFS, ProjectNotFoundError
from roboco.core.team_manager import TeamManager
from roboco.core.task_manager import TaskManager
from roboco.utils.id_generator import generate_short_id


class Project:
    """
    Project domain entity with data management capabilities.
    
    This class represents a project in the domain model, with both data
    representation and behavior. It encapsulates project metadata, tasks,
    and operations for loading, saving, and task execution.
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        fs: ProjectFS,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a project.
        
        Args:
            name: Name of the project
            description: Description of the project goals
            project_id: ID of the project
            id: Unique identifier for the project
            created_at: When the project was created
            updated_at: When the project was last updated
            teams: Teams involved in this project
            tasks: Tasks for the project
            source_code_dir: Directory for source code within the project directory
            docs_dir: Directory for documentation within the project directory
            metadata: Additional metadata for the project
            fs: Optional ProjectFS instance for file operations
        """
        # Initialize project metadata
        self.project_metadata = ProjectMetadata(
            id=id or generate_short_id(),
            name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            tasks=[],  # Tasks are stored separately as Task objects
            metadata=metadata or {}
        )
        
        # Store tasks as Task objects
        self.tasks = []
        
        # Initialize file system if not provided
        self.fs = fs or ProjectFS(project_id=project_id)
        
        # Initialize team manager for task execution
        self._team_manager = TeamManager(self.fs)
        
        # Initialize task manager for task operations 
        self._task_manager = TaskManager(self.fs)
    
    # Property accessors for common metadata fields
    @property
    def id(self) -> str:
        """Get the project ID."""
        return self.project_metadata.id
    
    @property
    def name(self) -> str:
        """Get the project name."""
        return self.project_metadata.name
    
    @name.setter
    def name(self, value: str):
        """Set the project name."""
        self.project_metadata.name = value
        self.project_metadata.updated_at = datetime.now()
    
    @property
    def description(self) -> str:
        """Get the project description."""
        return self.project_metadata.description
    
    @description.setter
    def description(self, value: str):
        """Set the project description."""
        self.project_metadata.description = value
        self.project_metadata.updated_at = datetime.now()
    
    @property
    def project_id(self) -> str:
        """Get the project ID (same as directory name)."""
        return self.project_metadata.id
    
    @property
    def created_at(self) -> str:
        """Get the project creation time."""
        return self.project_metadata.created_at
    
    @property
    def updated_at(self) -> str:
        """Get the project update time."""
        return self.project_metadata.updated_at
    
    @updated_at.setter
    def updated_at(self, value: str):
        """Set the project update time."""
        self.project_metadata.updated_at = value
    
    @property
    def teams(self) -> List[str]:
        """Get the teams involved in the project."""
        return self.project_metadata.teams
    
    @property
    def source_code_dir(self) -> str:
        """Get the source code directory."""
        return self.project_metadata.source_code_dir
    
    @property
    def docs_dir(self) -> str:
        """Get the documentation directory."""
        return self.project_metadata.docs_dir
    
    @property
    def team_manager(self) -> TeamManager:
        """Get the team manager instance, initializing it if needed."""
        return self._team_manager
    
    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update a metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.project_metadata.metadata[key] = value
        self.project_metadata.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the project to a dictionary.
        
        Returns:
            Dictionary representation of the project
        """
        # Convert project metadata to dict
        result = self.project_metadata.dict()
        
        # Update with tasks
        result["tasks"] = [task.dict() if hasattr(task, 'dict') else task for task in self.tasks]
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], fs: Optional[ProjectFS] = None) -> 'Project':
        """
        Create a project from a dictionary.
        
        Args:
            data: Dictionary representation of the project
            fs: Optional ProjectFS instance for file operations
            
        Returns:
            Project instance
        """
        # Convert task dictionaries to Task objects
        tasks = []
        for task_data in data.get("tasks", []):
            if isinstance(task_data, dict):
                tasks.append(Task(**task_data))
            else:
                tasks.append(task_data)
        
        # Create ProjectFS if not provided
        if not fs and data.get("project_id"):
            fs = ProjectFS(project_id=data.get("project_id"))
        
        project_id = data.get("project_id")
        
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            metadata=data.get("metadata", {}),
            fs=fs
        )
    
    def save(self) -> None:
        """
        Save the project to project.json.
        
        This method converts the project to a dictionary and then saves it
        to project.json using the project's file system.
        """
        project_data = self.to_dict()
        
        # Ensure required fields are present
        required_fields = ["name", "description", "id"]
        for field in required_fields:
            if field not in project_data:
                raise ValueError(f"Required field '{field}' is missing from project data")
        
        # Ensure the project has an id
        if "id" not in project_data:
            project_data["id"] = generate_short_id()
            logger.info(f"Adding missing id {project_data['id']} to project {project_data['name']}")
        
        # Update timestamp
        project_data["updated_at"] = datetime.now().isoformat()
        
        # Write to project.json
        json_content = json.dumps(project_data, indent=2)
        self.fs.write_sync("project.json", json_content)
        
        logger.info(f"Saved project {self.id} to {self.project_id}/project.json")
    
    @classmethod
    def load(cls, project_id: str) -> 'Project':
        """
        Load a project from project.json.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Project instance
            
        Raises:
            ProjectNotFoundError: If the project.json file does not exist
        """
        # Create file system
        fs = ProjectFS(project_id=project_id)
        
        try:
            # Load project data
            project_data = fs.get_project_data()
            
            if not project_data:
                raise ProjectNotFoundError(f"Empty project data in {project_id}/project.json")
            
            return cls.from_dict(project_data, fs)
        except FileNotFoundError:
            raise ProjectNotFoundError(f"Project not found: {project_id}/project.json")
    
    def load_tasks(self) -> List[Task]:
        """
        Load tasks from tasks.md.
        
        Returns:
            List of Task objects
        """
        # Use the task manager to load tasks
        self.tasks = self._task_manager.load_tasks()
        return self.tasks
        
    def mark_task_completed(self, task: Task) -> bool:
        """
        Mark a specific task as completed in tasks.md.
        Updates only the task status without destroying file content.
        
        Args:
            task: The task to mark as completed
            
        Returns:
            True if the task was successfully marked, False otherwise
        """
        # Use the task manager to mark the task as completed
        return self._task_manager.mark_task_completed(task)
    
    def _convert_to_dict(self, obj):
        """
        Convert a potentially non-serializable object to a dictionary.
        
        This handles special cases like Autogen's ChatResult class.
        
        Args:
            obj: Object to convert
            
        Returns:
            Dictionary representation that's JSON serializable
        """
        if obj is None:
            return None
            
        # If it's already a dict, just return it
        if isinstance(obj, dict):
            # Process each value in the dict recursively
            return {k: self._convert_to_dict(v) for k, v in obj.items()}
            
        # If it's a list, convert each item
        if isinstance(obj, list):
            return [self._convert_to_dict(item) for item in obj]
            
        # Handle ChatResult from Autogen
        if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ChatResult':
            result = {
                'summary': getattr(obj, 'summary', ''),
                'cost': getattr(obj, 'cost', 0),
            }
            
            # Handle chat_history
            if hasattr(obj, 'chat_history'):
                if isinstance(obj.chat_history, list):
                    result['chat_history'] = self._convert_to_dict(obj.chat_history)
                else:
                    result['chat_history'] = str(obj.chat_history)
                    
            return result
            
        # For any other object with attributes, convert to dict if possible
        if hasattr(obj, '__dict__'):
            return {k: self._convert_to_dict(v) for k, v in obj.__dict__.items() 
                    if not k.startswith('_')}
            
        # For basic types (str, int, float, bool, etc.)
        # Just return as is, as they're already serializable
        try:
            # Test if it's JSON serializable
            import json
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            # If not serializable, convert to string
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
        if task.status == TaskStatus.DONE:
            logger.info(f"Task '{task.description}' is already marked as completed, skipping execution")
            return {
                "task": task.description,
                "status": "already_completed"
            }
        
        # Create and log an outstanding header for this task
        task_header = self._task_manager.create_task_header(task)
        logger.info(task_header)
        logger.info(f"Executing task: {task.description}")
        
        # Get appropriate team for this task
        team = self.team_manager.get_team_for_task(task)
        
        # Get minimal context using the task manager
        project_info = {
            "name": self.name,
            "description": self.description,
            "id": self.project_id,
            "source_code_dir": self.source_code_dir,
            "docs_dir": self.docs_dir
        }
        execution_context = self._task_manager.generate_task_context(task, self.tasks, project_info)
        
        # Track results
        results = {
            "task": task.description,
            "status": "success"
        }
        
        try:
            # Format the task prompt
            task_prompt = f"""
Task: {task.description}

Details:
{chr(10).join([f"* {detail}" for detail in task.details]) if task.details else "No additional details provided."}

CONTEXT:
{execution_context}

Instructions:
- You have access to the filesystem tool for all file operations
- Use the filesystem tool's commands to:
    * `list_directory` to explore directories and see what files exist
    * `read_file` to read file contents
    * `save_file` to create or modify files
    * `file_exists` to check if a file exists
    * `create_directory` to create new directories
    * `delete_file` to remove files
    * `read_json` to read and parse JSON files
- IMPORTANT: All file paths must be relative to the project root. DO NOT include the project ID in any path
- For example, use "src/main.py" not "{self.project_id}/src/main.py"
- Always place source code files (js, py, etc.) in the src directory
- Always place documentation files (md, txt, etc.) in the docs directory
- The root directory already exists (it's the project directory)
- Always use simple paths: "src/file.py", "docs/readme.md", etc.
- Maintain a clean, organized directory structure
- Do not create files directly in the project root
- When modifying files, use the filesystem tool's commands instead of trying to edit files directly
"""
            
            # Execute task using the team
            task_result = await team.run_chat(query=task_prompt)
            
            # Convert any non-serializable objects to dictionaries
            task_result = self._convert_to_dict(task_result)
            
            # Update task status based on result
            if "error" not in task_result:
                task.status = TaskStatus.DONE
                task.completed_at = datetime.now().isoformat()
                
                # Mark task as completed in tasks.md
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
                logger.error(f"Task '{task.description}' failed: {task_result.get('error', 'Unknown error')}")
            
        except Exception as e:
            error_details = traceback.format_exc()
            results.update({
                "status": "failed",
                "error": str(e),
                "error_details": error_details
            })
            logger.error(f"Exception executing task '{task.description}': {e}")
            logger.error(f"Traceback: {error_details}")
        
        # Add completion header
        completion_header = self._task_manager.create_task_completion_header(task, results["status"])
        logger.info(completion_header)
        
        logger.info(f"Task '{task.description}' execution completed with status: {results['status']}")
        return results 

    async def execute_tasks(self, keyword_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute all tasks in the project, optionally filtered by a keyword.
        Fails immediately if any task fails.
        
        Args:
            keyword_filter: Optional keyword to filter tasks by description
            
        Returns:
            Dictionary containing execution results
        """
        # Make sure tasks are loaded
        if not self.tasks:
            self.load_tasks()
        
        if not self.tasks:
            error_msg = "No tasks found in the project"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.info(f"Found {len(self.tasks)} tasks in project")
        
        # Filter tasks if needed
        tasks_to_execute = self.tasks
        if keyword_filter:
            logger.info(f"Filtering tasks by keyword: {keyword_filter}")
            filtered_tasks = [t for t in self.tasks if keyword_filter.lower() in t.description.lower()]
            if not filtered_tasks:
                error_msg = f"No tasks matching '{keyword_filter}' found"
                logger.error(error_msg)
                return {"error": error_msg}
            tasks_to_execute = filtered_tasks
            logger.info(f"Filtered to {len(tasks_to_execute)} tasks")
        
        # Track results
        results = {
            "tasks": {},
            "status": "success"
        }
        
        # Track completion stats
        completed_count = 0
        
        # Execute each task
        for task in tasks_to_execute:
            task_result = await self.execute_task(task)
            
            # Convert result to ensure it's serializable
            task_result = self._convert_to_dict(task_result)
            
            results["tasks"][task.description] = task_result
            
            # Update completion stats
            if task_result["status"] == "completed" or task_result["status"] == "already_completed":
                completed_count += 1
            else:
                # Task failed, stop execution immediately
                results["status"] = "failed"
                logger.error(f"Task '{task.description}' failed. Stopping further execution.")
                
                # Update the project's last updated time and save
                self.project_metadata.updated_at = datetime.now().isoformat()
                self.save()
                
                logger.info(f"Project tasks execution stopped with status: failed")
                return results
        
        # Create a summary of files created in each directory
        src_files = self.fs.list_sync(self.source_code_dir)
        docs_files = self.fs.list_sync(self.docs_dir)
        
        results["files"] = {
            self.source_code_dir: src_files,
            self.docs_dir: docs_files
        }
        
        # Update the project's last updated time and save
        self.project_metadata.updated_at = datetime.now().isoformat()
        self.save()
        
        logger.info(f"Project tasks execution completed with status: {results['status']}")
        return results
        
    @classmethod
    def initialize(
        cls,
        name: str,
        description: str,
        project_id: str,
        manifest: ProjectManifest,
        teams: Optional[List[str]] = None,
    ) -> 'Project':
        """
        Initialize a new project on disk.
        
        This method creates a project structure with appropriate
        directories and files. It processes the project manifest,
        creates the necessary file structure, and returns a Project instance.
        
        Args:
            name: Project name
            description: Project description
            project_id: Optional project ID
            teams: Optional list of teams to use
            manifest: Optional project manifest
            
        Returns:
            Project instance for the newly created project
        """
        # If the manifest is a dictionary, convert it to a ProjectManifest
        if isinstance(manifest, dict):
            manifest = dict_to_project_manifest(manifest)
        
        # Use manifest's ID if available, otherwise use the provided project_id
        project_id = manifest.id if manifest.id else project_id
        logger.debug(f"Using project_id: {project_id}")
        
        # Create ProjectFS for the new project
        fs = ProjectFS(project_id=project_id)
        
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
        
        logger.info(f"Created project '{name}' in directory: {project_id}")
        return cls(
            id=project_id,
            name=name,
            description=description,
            fs=fs,
            metadata=manifest.meta
        ) 