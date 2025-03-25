"""
Project FileSystem

This module provides a specialized FileSystem implementation for projects,
combining the ease of use of the FileSystem abstraction with the domain-specific
functionality of project repositories.

It includes:
- FileSystem: A base class for file operations with directory context
- ProjectFS: A specialized filesystem for project management
"""

import os
import json
import re
import shutil
from pathlib import Path
from typing import Optional, List, Union, Dict, Any, BinaryIO, TextIO
from datetime import datetime
import uuid
import yaml
from loguru import logger

from roboco.utils import (
    ensure_directory,
    read_file, 
    write_file,
    append_to_file,
    delete_file,
    list_files,
    read_json_file,
    write_json_file,
    read_yaml_file,
    write_yaml_file,
    copy_file,
    move_file,
    get_file_info
)
from roboco.core.models.project import Project
from roboco.core.models.task import Task
from roboco.core.config import load_config
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest


class FileSystem:
    """
    A file system abstraction that maintains a base directory context.
    
    This class provides simplified methods for file operations within a specific directory,
    handling path resolution and error handling automatically.
    """
    
    def __init__(self, base_dir: Union[str, Path]):
        """
        Initialize the file system with a base directory.
        
        Args:
            base_dir: The base directory for all file operations
        """
        self.base_dir = Path(base_dir)
        self._ensure_base_dir_exists()
    
    def _ensure_base_dir_exists(self) -> None:
        """Ensure the base directory exists."""
        ensure_directory(self.base_dir)
    
    def _resolve_path(self, rel_path: Union[str, Path]) -> Path:
        """
        Resolve a relative path to an absolute path within the base directory.
        
        Args:
            rel_path: A path relative to the base directory
            
        Returns:
            The absolute path
        """
        # Convert to Path if not already
        path = Path(rel_path)
        
        # Check for path traversal attempts
        if '..' in str(path):
            normalized = os.path.normpath(str(path))
            if normalized.startswith('..') or normalized.startswith('/'):
                raise ValueError(f"Path traversal attempt detected: {rel_path}")
        
        return self.base_dir / path
    
    async def read(self, rel_path: Union[str, Path], binary: bool = False) -> Optional[Union[str, bytes]]:
        """
        Read file contents from a path relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            binary: Whether to read in binary mode
            
        Returns:
            File contents or None if file doesn't exist or can't be read
        """
        abs_path = self._resolve_path(rel_path)
        return await read_file(abs_path, binary)
    
    async def write(self, rel_path: Union[str, Path], content: Union[str, bytes], binary: bool = False) -> bool:
        """
        Write content to a path relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            content: Content to write
            binary: Whether to write in binary mode
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        return await write_file(abs_path, content, binary)
    
    async def append(self, rel_path: Union[str, Path], content: Union[str, bytes], binary: bool = False) -> bool:
        """
        Append content to a file relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            content: Content to append
            binary: Whether to append in binary mode
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        return await append_to_file(abs_path, content, binary)
    
    async def delete(self, rel_path: Union[str, Path]) -> bool:
        """
        Delete a file or directory relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        return await delete_file(abs_path)
    
    async def ls(self, rel_path: Union[str, Path] = "", pattern: Optional[str] = None) -> List[str]:
        """
        List files in a directory relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            pattern: Optional glob pattern to filter files
            
        Returns:
            List of file paths relative to the specified directory
        """
        abs_path = self._resolve_path(rel_path)
        files = await list_files(abs_path, pattern)
        
        # Convert absolute paths back to relative paths
        base_str = str(self.base_dir)
        return [os.path.relpath(f, base_str) for f in files]
    
    async def exists(self, rel_path: Union[str, Path]) -> bool:
        """
        Check if a file or directory exists.
        
        Args:
            rel_path: Path relative to the base directory
            
        Returns:
            True if the path exists, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        return os.path.exists(abs_path)
    
    async def mkdir(self, rel_path: Union[str, Path]) -> bool:
        """
        Create a directory relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        try:
            ensure_directory(abs_path)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {abs_path}: {str(e)}")
            return False
    
    async def read_json(self, rel_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read and parse a JSON file relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            
        Returns:
            Parsed JSON data or None if reading failed
        """
        abs_path = self._resolve_path(rel_path)
        return await read_json_file(abs_path)
    
    async def write_json(self, rel_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Write data as JSON to a file relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            data: Data to write as JSON
            indent: Indentation level for JSON formatting
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        return await write_json_file(abs_path, data, indent)
    
    async def read_yaml(self, rel_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Read and parse a YAML file relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            
        Returns:
            Parsed YAML data or None if reading failed
        """
        abs_path = self._resolve_path(rel_path)
        return await read_yaml_file(abs_path)
    
    async def write_yaml(self, rel_path: Union[str, Path], data: Dict[str, Any]) -> bool:
        """
        Write data as YAML to a file relative to the base directory.
        
        Args:
            rel_path: Path relative to the base directory
            data: Data to write as YAML
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(rel_path)
        return await write_yaml_file(abs_path, data)
    
    async def copy(self, source_rel_path: Union[str, Path], target_rel_path: Union[str, Path]) -> bool:
        """
        Copy a file within the base directory.
        
        Args:
            source_rel_path: Source path relative to the base directory
            target_rel_path: Target path relative to the base directory
            
        Returns:
            True if successful, False otherwise
        """
        source_abs_path = self._resolve_path(source_rel_path)
        target_abs_path = self._resolve_path(target_rel_path)
        return await copy_file(source_abs_path, target_abs_path)
    
    async def move(self, source_rel_path: Union[str, Path], target_rel_path: Union[str, Path]) -> bool:
        """
        Move a file within the base directory.
        
        Args:
            source_rel_path: Source path relative to the base directory
            target_rel_path: Target path relative to the base directory
            
        Returns:
            True if successful, False otherwise
        """
        source_abs_path = self._resolve_path(source_rel_path)
        target_abs_path = self._resolve_path(target_rel_path)
        return await move_file(source_abs_path, target_abs_path)
    
    def info(self, rel_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """
        Get information about a file or directory.
        
        Args:
            rel_path: Path relative to the base directory
            
        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        abs_path = self._resolve_path(rel_path)
        file_info = get_file_info(abs_path)
        
        if file_info:
            # Convert absolute path to relative path
            file_info["rel_path"] = os.path.relpath(file_info["path"], str(self.base_dir))
        
        return file_info
    
    @property
    def path(self) -> Path:
        """Get the base directory path."""
        return self.base_dir


class ProjectNotFoundError(Exception):
    """Exception raised when a project is not found."""
    pass


class ProjectFS(FileSystem):
    """
    Project filesystem abstraction.
    
    This class extends the FileSystem class to provide project-specific
    functionality, such as project metadata management, task tracking,
    and artifact organization.
    """
    
    def __init__(self, project_id: str = None, project_dir: str = None):
        """
        Initialize the project filesystem.
        
        Either project_id or project_dir must be provided.
        
        Args:
            project_id: ID of the project (will be resolved to a directory)
            project_dir: Direct path to the project directory
        """
        if not project_id and not project_dir:
            raise ValueError("Either project_id or project_dir must be provided")
            
        # Load configuration to get projects base directory
        self.config = load_config()
        self.projects_base_dir = os.path.join(self.config.workspace_root, "projects")
        
        # If project_dir is provided, use it directly
        if project_dir:
            super().__init__(project_dir)
            self.project_id = self._get_project_id_from_dir(project_dir)
        # Otherwise, resolve the project ID to a directory
        else:
            project_dir = self._resolve_project_dir(project_id)
            super().__init__(project_dir)
            self.project_id = project_id
            
        # Cache for project data
        self._project_data = None
    
    def _get_project_id_from_dir(self, project_dir: str) -> Optional[str]:
        """
        Get the project ID from a directory by reading project.json.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            Project ID or None if not found
        """
        project_json_path = os.path.join(project_dir, "project.json")
        if os.path.exists(project_json_path):
            try:
                with open(project_json_path, 'r') as f:
                    data = json.load(f)
                    return data.get("id")
            except Exception as e:
                logger.error(f"Failed to read project ID from {project_json_path}: {str(e)}")
        return None
    
    def _resolve_project_dir(self, project_id: str) -> str:
        """
        Resolve a project ID to its directory path.
        
        This method searches for the project directory by:
        1. Checking if the ID is a direct directory name
        2. Searching all project directories for a matching ID in project.json
        
        Args:
            project_id: ID of the project
            
        Returns:
            Path to the project directory
            
        Raises:
            ProjectNotFoundError: If the project directory cannot be found
        """
        # Check if project ID is actually a directory name already
        direct_path = os.path.join(self.projects_base_dir, project_id)
        if os.path.exists(direct_path) and os.path.isdir(direct_path):
            config_path = os.path.join(direct_path, "project.json")
            if os.path.exists(config_path):
                return direct_path
        
        # Otherwise, try to find by ID in project.json files
        for folder_name in os.listdir(self.projects_base_dir):
            folder_path = os.path.join(self.projects_base_dir, folder_name)
            if os.path.isdir(folder_path):
                config_path = os.path.join(folder_path, "project.json")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r") as f:
                            project_data = json.load(f)
                            if project_data.get("id") == project_id:
                                return folder_path
                    except Exception:
                        pass
        
        # Not found
        raise ProjectNotFoundError(f"Project with ID {project_id} not found")
    
    @classmethod
    def _create_folder_name(cls, project: Project) -> str:
        """
        Create a clean, meaningful folder name from a project.
        
        Args:
            project: The project to create a folder name for
            
        Returns:
            A suitable folder name
        """
        # If project has a specified directory, use that
        if project.directory and project.directory != project.id:
            folder_name = project.directory
        else:
            # Create a folder name from the project name
            folder_name = project.name.lower()
            
            # Replace special characters and spaces
            folder_name = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name)
            folder_name = re.sub(r'_+', '_', folder_name)  # Replace multiple underscores with single one
            folder_name = folder_name.strip('_')
            
            # Add a small prefix from the ID for uniqueness
            if project.id:
                id_prefix = project.id.split('-')[0] if '-' in project.id else project.id[:8]
                folder_name = f"{folder_name}_{id_prefix}"
        
        return folder_name
    
    async def get_project(self) -> Project:
        """
        Get the project data.
        
        Returns:
            Project object with the project data
        
        Raises:
            ProjectNotFoundError: If the project data cannot be found
        """
        if self._project_data:
            return self._project_data
            
        try:
            data = await self.read_json("project.json")
            if not data:
                raise ProjectNotFoundError(f"Project data not found at {self.path}")
                
            self._project_data = Project.from_dict(data)
            return self._project_data
        except Exception as e:
            raise ProjectNotFoundError(f"Failed to load project data: {str(e)}")
    
    async def save_project(self, project: Project) -> None:
        """
        Save project data.
        
        Args:
            project: Project object to save
            
        Returns:
            None
        """
        # Update the directory field to match the folder name
        project.directory = os.path.basename(self.path)
        
        # Update the project data
        project.updated_at = datetime.now()
        
        # Save the project data
        await self.write_json("project.json", project.to_dict())
        
        # Update the cache
        self._project_data = project
        
        # Update task.md
        await self._update_task_markdown(project)
    
    async def _update_task_markdown(self, project: Project) -> None:
        """
        Update the task.md file for a project.
        
        Args:
            project: The project to update the task.md for
        """
        content = f"# {project.name} - Task List\n\n"
        
        # Add project-level tasks
        if project.tasks:
            content += "## Project Tasks\n\n"
            for task in project.tasks:
                status_marker = "- [x]" if task.status == "DONE" else "- [ ]"
                content += f"{status_marker} **{task.description}**"
                if task.priority:
                    content += f" (Priority: {task.priority})"
                content += "\n"
                if task.assigned_to:
                    content += f"  - Assigned to: {task.assigned_to}\n"
                if task.depends_on:
                    content += f"  - Depends on: {', '.join(task.depends_on)}\n"
                if task.tags:
                    content += f"  - Tags: {', '.join(task.tags)}\n"
                if task.completed_at:
                    content += f"  - Completed at: {task.completed_at.isoformat()}\n"
                content += "\n"
        
        await self.write("task.md", content)
    
    async def add_task(self, task: Task) -> None:
        """
        Add a task to the project.
        
        Args:
            task: Task to add
            
        Returns:
            None
        """
        project = await self.get_project()
        project.tasks.append(task)
        await self.save_project(project)
    
    async def update_task(self, task_id: str, **kwargs) -> bool:
        """
        Update a task in the project.
        
        Args:
            task_id: ID of the task to update
            **kwargs: Task attributes to update
            
        Returns:
            True if the task was updated, False if not found
        """
        project = await self.get_project()
        
        for task in project.tasks:
            if task.id == task_id:
                # Update task properties
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # Special handling for status changes
                if "status" in kwargs and kwargs["status"] == "DONE" and not task.completed_at:
                    task.completed_at = datetime.now()
                
                # Save the project
                await self.save_project(project)
                return True
                
        return False
    
    @classmethod
    async def create(
        cls,
        name: str,
        description: str,
        directory: Optional[str] = None,
        teams: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> "ProjectFS":
        """
        Create a new project.
        
        Args:
            name: Name of the project
            description: Description of the project
            directory: Optional custom directory name
            teams: Teams involved in the project
            tags: Tags for the project
            
        Returns:
            ProjectFS instance for the new project
        """
        # Create a new project instance
        project = Project(
            name=name,
            description=description,
            directory=directory or name.lower().replace(" ", "_"),
            teams=teams or [],
            tags=tags or []
        )
        
        # Generate a unique ID
        project.id = str(uuid.uuid4())
        
        # Create a folder name
        folder_name = cls._create_folder_name(project)
        project.directory = folder_name
        
        # Get the projects base directory
        config = load_config()
        projects_base_dir = os.path.join(config.workspace_root, "projects")
        
        # Create the project directory
        project_dir = os.path.join(projects_base_dir, folder_name)
        
        # Create a ProjectFS instance
        project_fs = ProjectFS(project_dir=project_dir)
        
        # Ensure directories exist
        await project_fs.mkdir("")
        await project_fs.mkdir("src")
        await project_fs.mkdir("docs")
        
        # Save the project data
        await project_fs.save_project(project)
        
        return project_fs
    
    @classmethod
    async def list_all(cls) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all projects
        """
        # Get the projects base directory
        config = load_config()
        projects_base_dir = os.path.join(config.workspace_root, "projects")
        
        projects = []
        
        # Check if projects directory exists
        if not os.path.exists(projects_base_dir):
            return projects
        
        # Iterate through project directories
        for project_dir in os.listdir(projects_base_dir):
            project_path = os.path.join(projects_base_dir, project_dir)
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
    
    @classmethod
    async def find_by_name(cls, name: str) -> List[Project]:
        """
        Find projects by name.
        
        Args:
            name: Name to search for (case-insensitive partial match)
            
        Returns:
            List of matching projects
        """
        projects = await cls.list_all()
        return [p for p in projects if name.lower() in p.name.lower()]
    
    @classmethod
    async def find_by_tag(cls, tag: str) -> List[Project]:
        """
        Find projects by tag.
        
        Args:
            tag: Tag to search for (exact match)
            
        Returns:
            List of matching projects
        """
        projects = await cls.list_all()
        return [p for p in projects if tag in p.tags]
    
    @classmethod
    async def get_by_id(cls, project_id: str) -> "ProjectFS":
        """
        Get a project by its ID.
        
        Args:
            project_id: ID of the project
            
        Returns:
            ProjectFS instance for the project
            
        Raises:
            ProjectNotFoundError: If the project cannot be found
        """
        return ProjectFS(project_id=project_id)
    
    async def delete(self) -> bool:
        """
        Delete the project, removing all its files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the entire project directory
            return await super().delete("")
        except Exception as e:
            logger.error(f"Failed to delete project {self.project_id}: {str(e)}")
            return False

    async def execute_project_manifest(self, manifest: Union[ProjectManifest, Dict[str, Any]], override_base_path: str = "") -> Dict[str, Any]:
        """Execute a project manifest to create a complete project structure.
        
        Args:
            manifest: Project manifest containing directories and files to create
            override_base_path: Optional path within the project to use as base path
            
        Returns:
            Dict containing results of the operation
        """
        results = {
            "success": True,
            "created_directories": [],
            "created_files": [],
            "errors": []
        }
        
        try:
            # Convert dict to ProjectManifest if needed
            if isinstance(manifest, dict):
                try:
                    manifest = dict_to_project_manifest(manifest)
                except Exception as e:
                    results["errors"].append(f"Invalid project manifest format: {str(e)}")
                    results["success"] = False
                    return results
            
            # Create directories
            for directory in manifest.directories or []:
                dir_path = os.path.join(override_base_path, directory) if override_base_path else directory
                try:
                    await self.mkdir(dir_path)
                    results["created_directories"].append(directory)
                except Exception as e:
                    results["errors"].append(f"Error creating directory {directory}: {str(e)}")
                    results["success"] = False
            
            # Create files
            for file_info in manifest.files or []:
                file_path = os.path.join(override_base_path, file_info.path) if override_base_path else file_info.path
                content = file_info.content
                
                # Create parent directory if it doesn't exist
                parent_dir = os.path.dirname(file_path)
                if parent_dir:
                    try:
                        await self.mkdir(parent_dir)
                        # Only add if not already in the created directories list
                        if parent_dir not in results["created_directories"]:
                            results["created_directories"].append(parent_dir)
                    except Exception as e:
                        results["errors"].append(f"Error creating parent directory for {file_info.path}: {str(e)}")
                        results["success"] = False
                        continue
                
                try:
                    await self.write(file_path, content)
                    results["created_files"].append(file_info.path)
                except Exception as e:
                    results["errors"].append(f"Error creating file {file_info.path}: {str(e)}")
                    results["success"] = False
        
        except Exception as e:
            results["errors"].append(f"Error executing project manifest: {str(e)}")
            results["success"] = False
        
        return results


# Function to get a ProjectFS instance for a project
def get_project_fs(project_id: str) -> ProjectFS:
    """
    Get a ProjectFS instance for a specific project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        ProjectFS instance for the project
        
    Raises:
        ProjectNotFoundError: If the project cannot be found
    """
    return ProjectFS(project_id=project_id) 