"""
Project FileSystem

This module provides a specialized FileSystem implementation for projects,
providing file operations within a project directory context.

It includes:
- ProjectFS: File system operations with project directory context
"""

import os
import json
import re
from pathlib import Path
from typing import Optional, List, Union, Dict, Any
from datetime import datetime
import uuid
from loguru import logger
import shutil

from roboco.core.config import load_config, get_workspace
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.utils.id_generator import generate_short_id


class ProjectNotFoundError(Exception):
    """Exception raised when a project cannot be found."""
    pass


class ProjectFS:
    """
    File system operations with project directory context.
    
    This class wraps file system operations, providing a context-aware API
    for reading, writing, and managing files within a project directory.
    
    Attributes:
        base_dir: The base directory for all operations
    """

    def __init__(self, project_id: str):
        """
        Initialize the ProjectFS.
        
        Args:
            project_id: The project ID (used as the directory name)
        """
        # If the directory is absolute, use it directly
        if os.path.isabs(project_id):
            self.base_dir = Path(project_id)
        else:
            # Otherwise, assume it's relative to the workspace
            config = load_config()
            workspace_dir = get_workspace(config)
            self.base_dir = Path(workspace_dir) / project_id
        
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
        
    def write_file(self, path: str, content: str) -> bool:
        """
        Write content to a file.
        
        This is an alias for write_sync for better readability.
        
        Args:
            path: File path relative to base_dir
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        return self.write_sync(path, content)
        
    # These methods keep the async interface for backwards compatibility
    # but internally use the sync methods
    async def mkdir(self, path: str) -> bool:
        """
        Create a directory (async wrapper).
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        return self.mkdir_sync(path)
        
    async def exists(self, path: str) -> bool:
        """
        Check if a file or directory exists (async wrapper).
        
        Args:
            path: File/directory path relative to base_dir
            
        Returns:
            True if exists, False otherwise
        """
        return self.exists_sync(path)
        
    async def is_dir(self, path: str) -> bool:
        """
        Check if a path is a directory (async wrapper).
        
        Args:
            path: Path relative to base_dir
            
        Returns:
            True if directory, False otherwise
        """
        return self.is_dir_sync(path)
        
    async def read(self, path: str) -> str:
        """
        Read the contents of a file (async wrapper).
        
        Args:
            path: File path relative to base_dir
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If the file does not exist
        """
        return self.read_sync(path)
        
    async def write(self, path: str, content: str) -> bool:
        """
        Write content to a file (async wrapper).
        
        Args:
            path: File path relative to base_dir
            content: Content to write
            
        Returns:
            True if successful, False otherwise
        """
        return self.write_sync(path, content)
        
    async def append(self, path: str, content: str) -> bool:
        """
        Append content to a file (async wrapper).
        
        Args:
            path: File path relative to base_dir
            content: Content to append
            
        Returns:
            True if successful, False otherwise
        """
        return self.append_sync(path, content)
        
    async def delete(self, path: str) -> bool:
        """
        Delete a file or directory (async wrapper).
        
        Args:
            path: Path relative to base_dir
            
        Returns:
            True if successful, False otherwise
        """
        return self.delete_sync(path)
        
    async def list(self, path: str = "") -> List[str]:
        """
        List files and directories in a directory (async wrapper).
        
        Args:
            path: Directory path relative to base_dir
            
        Returns:
            List of file/directory names
            
        Raises:
            NotADirectoryError: If the path is not a directory
        """
        return self.list_sync(path)
        
    async def read_json(self, path: str) -> Dict[str, Any]:
        """
        Read and parse a JSON file (async wrapper).
        
        Args:
            path: File path relative to base_dir
            
        Returns:
            Parsed JSON data as Python object
            
        Raises:
            FileNotFoundError: If the file does not exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        return self.read_json_sync(path)

    def get_project_data(self) -> Dict[str, Any]:
        """
        Get project data from project.json.
        
        This is a convenience method to get the project data from the
        project.json file in the project directory.
        
        Returns:
            Project data as a dictionary
            
        Raises:
            FileNotFoundError: If project.json does not exist
            json.JSONDecodeError: If project.json contains invalid JSON
        """
        return self.read_json_sync("project.json")


def get_project_fs(project_id: Optional[str] = None) -> ProjectFS:
    """
    Factory function to get a ProjectFS instance.
    
    This is a convenience function that handles configuration loading and
    creating the appropriate ProjectFS with the workspace context.
    
    Args:
        project_id: Project ID to use for the file system. If None, creates a temporary one.
        
    Returns:
        A ProjectFS instance for the specified project
    """
    # If no project_id is provided, generate a temporary one
    if not project_id:
        project_id = f"temp_{generate_short_id()}"
    
    # Return a ProjectFS instance
    return ProjectFS(project_id=project_id) 