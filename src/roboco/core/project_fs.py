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
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
import uuid
from loguru import logger

from roboco.core.models.project import Project
from roboco.core.models.task import Task
from roboco.core.config import load_config, get_workspace
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest


class FileSystem:
    """
    Base class for file system operations with directory context.
    
    This class wraps file system operations, providing a context-aware API
    for reading, writing, and managing files within a base directory.
    
    Attributes:
        base_dir: The base directory for all operations
    """

    def __init__(self, base_dir: str):
        """
        Initialize the FileSystem.
        
        Args:
            base_dir: The base directory for all operations
        """
        self.base_dir = Path(base_dir)
        
    def _resolve_path(self, path: str) -> str:
        """
        Resolve a path relative to the base directory.
        
        This method ensures that the path is within the base directory,
        preventing directory traversal attacks.
        
        Args:
            path: The path to resolve, relative to the base directory
            
        Returns:
            The absolute path within the base directory
            
        Raises:
            ValueError: If the path would resolve outside the base directory
        """
        # Handle empty path
        if not path or path == "":
            return str(self.base_dir)
            
        # Convert to absolute path
        abs_path = (self.base_dir / path).resolve()
        
        # Check if the resolved path is within base_dir
        try:
            abs_path.relative_to(self.base_dir)
        except ValueError:
            raise ValueError(f"Path '{path}' would resolve outside the base directory")
            
        return str(abs_path)
        
    # Synchronous methods for basic file operations
    def mkdir_sync(self, path: str) -> bool:
        """
        Create a directory.
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(path)
        try:
            os.makedirs(abs_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {str(e)}")
            return False
            
    def exists_sync(self, path: str) -> bool:
        """
        Check if a file or directory exists.
        
        Args:
            path: File/directory path relative to base_dir
            
        Returns:
            True if exists, False otherwise
        """
        abs_path = self._resolve_path(path)
        return os.path.exists(abs_path)
        
    def is_dir_sync(self, path: str) -> bool:
        """
        Check if a path is a directory.
        
        Args:
            path: Path relative to base_dir
            
        Returns:
            True if directory, False otherwise
        """
        abs_path = self._resolve_path(path)
        return os.path.isdir(abs_path)
        
    def read_sync(self, path: str) -> str:
        """
        Read the contents of a file.
        
        Args:
            path: File path relative to base_dir
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        abs_path = self._resolve_path(path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def write_sync(self, path: str, content: str) -> bool:
        """
        Write content to a file.
        
        Args:
            path: File path relative to base_dir
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(path)
        try:
            # Ensure the parent directory exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Write the file
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write to {path}: {str(e)}")
            return False
            
    def append_sync(self, path: str, content: str) -> bool:
        """
        Append content to a file.
        
        Args:
            path: File path relative to base_dir
            content: Content to append
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(path)
        try:
            # Ensure the parent directory exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Append to the file
            with open(abs_path, 'a', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to append to {path}: {str(e)}")
            return False
            
    def delete_sync(self, path: str) -> bool:
        """
        Delete a file or directory.
        
        Args:
            path: Path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        abs_path = self._resolve_path(path)
        try:
            if os.path.isdir(abs_path):
                # Use os.rmdir for empty directories
                os.rmdir(abs_path)
            elif os.path.isfile(abs_path):
                os.remove(abs_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete {path}: {str(e)}")
            return False
            
    def list_sync(self, path: str) -> List[str]:
        """
        List files and directories in a directory.
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            List of file/directory names
            
        Raises:
            NotADirectoryError: If the path is not a directory
        """
        abs_path = self._resolve_path(path)
        if not os.path.isdir(abs_path):
            raise NotADirectoryError(f"Path {path} is not a directory")
        return os.listdir(abs_path)
        
    def read_json_sync(self, path: str) -> Dict[str, Any]:
        """
        Read and parse a JSON file.
        
        Args:
            path: File path relative to base_dir
            
        Returns:
            Parsed JSON data as Python object
            
        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        content = self.read_sync(path)
        # Handle empty files gracefully
        if not content or content.isspace():
            return {}
        return json.loads(content)
        
    # These methods keep the async interface for backwards compatibility
    # but internally use the sync methods
    async def mkdir(self, path: str) -> bool:
        """
        Create a directory.
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        return self.mkdir_sync(path)
    
    async def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists.
        
        Args:
            path: File/directory path relative to base_dir
            
        Returns:
            True if exists, False otherwise
        """
        return self.exists_sync(path)
    
    async def is_dir(self, path: str) -> bool:
        """
        Check if a path is a directory.
        
        Args:
            path: Path relative to base_dir
            
        Returns:
            True if directory, False otherwise
        """
        return self.is_dir_sync(path)
    
    async def read(self, path: str) -> str:
        """
        Read the contents of a file.
        
        Args:
            path: File path relative to base_dir
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        return self.read_sync(path)
        
    async def read_json(self, path: str) -> Dict[str, Any]:
        """
        Read and parse a JSON file.
        
        Args:
            path: File path relative to base_dir
            
        Returns:
            Parsed JSON data as Python object
            
        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        return self.read_json_sync(path)
    
    async def write(self, path: str, content: str) -> bool:
        """
        Write content to a file.
        
        Args:
            path: File path relative to base_dir
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        return self.write_sync(path, content)
    
    async def append(self, path: str, content: str) -> bool:
        """
        Append content to a file.
        
        Args:
            path: File path relative to base_dir
            content: Content to append
            
        Returns:
            True if successful, False otherwise
        """
        return self.append_sync(path, content)
    
    async def delete(self, path: str) -> bool:
        """
        Delete a file or directory.
        
        Args:
            path: Path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        return self.delete_sync(path)
    
    async def list(self, path: str = "") -> List[str]:
        """
        List files and directories in a directory.
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            List of file/directory names
            
        Raises:
            NotADirectoryError: If the path is not a directory
        """
        return self.list_sync(path)

    def rmdir_sync(self, path: str) -> bool:
        """
        Recursively remove a directory and all its contents.
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            NotADirectoryError: If the path is not a directory
            OSError: If removal fails
        """
        abs_path = self._resolve_path(path)
        
        if not os.path.isdir(abs_path):
            raise NotADirectoryError(f"Path {path} is not a directory")
            
        try:
            # Walk through directory tree bottom-up
            for root, dirs, files in os.walk(abs_path, topdown=False):
                # First remove all files in current directory
                for name in files:
                    file_path = os.path.join(root, name)
                    os.remove(file_path)
                    
                # Then remove all subdirectories
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    os.rmdir(dir_path)
                    
            # Finally remove the root directory
            os.rmdir(abs_path)
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove directory {path}: {str(e)}")
            return False

    async def rmdir(self, path: str) -> bool:
        """
        Recursively remove a directory and all its contents.
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        return self.rmdir_sync(path)


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
    
    def __init__(self, project_dir: str):
        """
        Initialize the project filesystem.
        
        If project_dir is empty, the project will be created in the projects base directory.
        
        Args:
            project_dir: Direct path to the project directory
        """

            
        # Load configuration to get projects base directory
        self.config = load_config()
        self.project_dir = project_dir
        
        # If project_dir is provided, use it directly
        super().__init__(get_workspace(self.config) / self.project_dir)
            
        # Cache for project data
        self._project_data = None
    
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
            
        data = await self.read_json("project.json")
        if not data:
            raise ProjectNotFoundError(f"Project data not found at {self.base_dir}")
            
        self._project_data = Project.from_dict(data)
        return self._project_data
    
    async def save_project(self, project: Project) -> None:
        """
        Save project data.
        
        Args:
            project: Project object to save
            
        Returns:
            None
        """
        # Update the directory field to match the folder name
        project.directory = os.path.basename(self.base_dir)
        
        # Update the project data
        project.updated_at = datetime.now()
        
        # Save the project data as properly serialized JSON
        await self.write("project.json", json.dumps(project.to_dict(), indent=2))
        
        # Update the cache
        self._project_data = project
    
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
        projects_base_dir = get_workspace(config)
        
        # Create the project directory
        project_dir = os.path.join(projects_base_dir, folder_name)
        
        # Create a ProjectFS instance
        project_fs = ProjectFS(project_dir=project_dir)
        
        try:
            # Create base directories
            await project_fs._ensure_directories()
            
            # Save the project data
            await project_fs.save_project(project)
            
            return project_fs
            
        except Exception as e:
            # If anything fails during setup, clean up by removing the project directory
            await project_fs.rmdir("")
            raise e

    async def _ensure_directories(self) -> None:
        """
        Ensure the base project directory exists.
        """
        # Create only the base project directory
        await self.mkdir("")

    @classmethod
    async def list_all(cls) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all projects
        """
        # Get the projects base directory
        config = load_config()
        projects_base_dir = get_workspace(config)
        
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
            # Use rmdir instead of delete for recursive directory removal
            return await self.rmdir("")
        except Exception as e:
            logger.error(f"Failed to delete project: {str(e)}")
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