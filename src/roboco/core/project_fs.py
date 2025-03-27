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
import shutil

from roboco.core.config import load_config, get_workspace
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.utils.id_generator import generate_short_id


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
    functionality, such as project metadata management and structure initialization.
    """
    
    def __init__(self, project_dir: str):
        """
        Initialize the project filesystem.
        
        Args:
            project_dir: Direct path to the project directory
        """
        # Load configuration to get projects base directory
        self.config = load_config()
        self.project_dir = project_dir
        
        # Initialize with the base directory
        workspace_root = get_workspace(self.config)
        super().__init__(os.path.join(workspace_root, self.project_dir))
            
        # Cache for project data
        self._project_data = None
    
    def get_project(self) -> Dict[str, Any]:
        """
        Get the project data.`
        
        Returns:
            Dictionary containing the project data
        
        Raises:
            ProjectNotFoundError: If the project data cannot be found
        """
        if self._project_data:
            return self._project_data
            
        try:
            data = self.read_json_sync("project.json")
            if not data:
                logger.error(f"Project data is empty in {self.base_dir}/project.json")
                raise ProjectNotFoundError(f"Project data is empty at {self.base_dir}")
            
            # Also log the data for debugging
            logger.debug(f"Read project data from {self.base_dir}/project.json: {data}")
            
            # Add project_dir if missing
            if "project_dir" not in data:
                base_dir_name = os.path.basename(self.base_dir)
                data["project_dir"] = base_dir_name
                logger.info(f"Added missing project_dir field: {base_dir_name}")
                
                # Save the updated data
                self.write_sync("project.json", json.dumps(data, indent=2))
            
            self._project_data = data
            return self._project_data
        except FileNotFoundError:
            logger.error(f"Project file not found at {self.base_dir}/project.json")
            raise ProjectNotFoundError(f"Project file not found at {self.base_dir}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in project file at {self.base_dir}/project.json")
            raise ProjectNotFoundError(f"Invalid JSON in project file at {self.base_dir}")
        except Exception as e:
            logger.error(f"Error reading project data from {self.base_dir}: {str(e)}")
            raise ProjectNotFoundError(f"Error reading project data: {str(e)}")
    
    def save_project(self, project_data: Dict[str, Any]) -> None:
        """
        Update and save project metadata to project.json.
        
        Args:
            project_data: Updated project data to save
        """
        # Ensure required fields are present
        required_fields = ["name", "description", "project_dir"]
        for field in required_fields:
            if field not in project_data:
                raise ValueError(f"Required field '{field}' is missing from project data")
                
        # Ensure the project has an id
        if "id" not in project_data:
            project_data["id"] = generate_short_id()
            logger.info(f"Adding missing id {project_data['id']} to project {project_data['name']}")
        
        # Update timestamp
        project_data["updated_at"] = datetime.now().isoformat()
        
        # Write the updated data back to project.json
        self.write_sync("project.json", json.dumps(project_data, indent=2))
        
        logger.debug(f"Saved project data to {self.base_dir}/project.json")
        
        # Enable writing further files
        self._project_data = project_data
    
    @classmethod
    def initialize(
        cls,
        name: str,
        description: str,
        project_dir: Optional[str] = None,
        teams: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        manifest: Optional[Union[ProjectManifest, Dict[str, Any]]] = None
    ) -> "ProjectFS":
        """
        Initialize a new project with the necessary structure and metadata.
        
        Args:
            name: Name of the project
            description: Description of the project
            project_dir: Optional directory name (defaults to name with underscores)
            teams: Optional list of team names
            tags: Optional list of tags
            manifest: Optional complete project manifest (if provided, other args are ignored)
                     File paths in the manifest can be either:
                     - Relative to the project directory (preferred)
                     - Prefixed with the project directory name (will be made relative)
            
        Returns:
            ProjectFS instance for the new project
        """
        # Generate project ID
        project_id = generate_short_id()
        now = datetime.now().isoformat()
        
        # Load config and get workspace root
        config = load_config()
        workspace_root = get_workspace(config)
        
        # If a complete manifest is provided, use that
        if manifest:
            if isinstance(manifest, dict):
                manifest = dict_to_project_manifest(manifest)
        else:
            # If no directory specified, generate from name
            if not project_dir:
                project_dir = name.lower().replace(' ', '_')
            
            # Create a project manifest
            manifest = ProjectManifest(
                name=name,
                description=description,
                project_dir=project_dir,
                structure={"type": "standard"},
                folder_structure=["src", "docs"],
                meta={
                    "teams": teams or [],
                    "tags": tags or []
                }
            )
        
        # Extract values from manifest
        name = manifest.name
        description = manifest.description
        project_dir = manifest.project_dir
        
        # Extract/convert structure information
        structure = {
            "type": manifest.structure.get("type", "standard"),
            "folder_structure": manifest.folder_structure,
            "files": [
                {"path": file.path, "content": file.content} 
                for file in (manifest.files or [])
            ]
        }
        
        # Set default directories from manifest or use standard defaults
        source_code_dir = "src"  # Default
        docs_dir = "docs"  # Default
        
        # Optional metadata might contain these settings
        if manifest.meta:
            source_code_dir = manifest.meta.get("source_code_dir", source_code_dir)
            docs_dir = manifest.meta.get("docs_dir", docs_dir)
        
        # Validate required parameters
        if not name or not description:
            raise ValueError("Project name and description are required in manifest")
        
        # Create the project data as a dictionary (no Project class dependency)
        project_data = {
            "id": project_id,  # Always include the id
            "name": name,
            "description": description,
            "project_dir": project_dir,
            "created_at": now,
            "updated_at": now,
            "teams": manifest.meta.get("teams", []) if manifest.meta else [],
            "jobs": manifest.meta.get("jobs", []) if manifest.meta else [],
            "tasks": manifest.meta.get("tasks", []) if manifest.meta else [],
            "tags": manifest.meta.get("tags", []) if manifest.meta else [],
            "source_code_dir": source_code_dir,
            "docs_dir": docs_dir,
            "metadata": manifest.meta or {}
        }
        
        # Create project directory structure
        full_project_dir = os.path.join(workspace_root, project_dir)
        
        if os.path.exists(full_project_dir):
            logger.warning(f"Project directory already exists: {full_project_dir} - Deleting it before proceeding")
            shutil.rmtree(full_project_dir)
        
        # Create ProjectFS for the new project
        project_fs = cls(project_dir=project_dir)
        
        # Create basic directory structure using ProjectFS methods instead of direct OS calls
        # First ensure the project root directory exists
        os.makedirs(full_project_dir, exist_ok=True)
        
        # Then use project_fs methods to create subdirectories
        project_fs.mkdir_sync(source_code_dir)
        project_fs.mkdir_sync(docs_dir)
        
        # Save the project metadata to project.json using ProjectFS
        project_fs.write_sync('project.json', json.dumps(project_data, indent=2))
        
        # Create tasks.md with empty content or from manifest tasks
        tasks_content = f"# {name}\n\n"
        if project_data["tasks"]:
            # Create tasks.md with the tasks from the manifest
            for task in project_data["tasks"]:
                # Get task status and description
                status = task.get("status", "TODO")
                checkbox = "[x]" if status.upper() == "DONE" else "[ ]"
                description = task.get("description", "")
                
                # Write the high-level task
                tasks_content += f"- {checkbox} {description}\n"
                
                # Write the task details
                details = task.get("details", [])
                for detail in details:
                    tasks_content += f"  * {detail}\n"
                
                # Add a blank line between tasks
                tasks_content += "\n"
        
        # Save tasks.md using ProjectFS
        project_fs.write_sync('tasks.md', tasks_content)
        
        # Create custom structure if provided
        if structure:
            # Create any additional directories
            if structure.get('folder_structure'):
                for folder in structure['folder_structure']:
                    if folder not in [source_code_dir, docs_dir]:  # Skip already created dirs
                        project_fs.mkdir_sync(folder)
                
            # Create any specified files
            if structure.get('files'):
                for file_info in structure['files']:
                    # Make path relative to project directory by removing project directory prefix if present
                    file_path = file_info['path']
                    
                    # If the path starts with the project directory name, remove it
                    if file_path.startswith(f"{project_dir}/") or file_path.startswith(f"{project_dir}\\"):
                        relative_path = file_path[len(project_dir)+1:]  # +1 for the slash
                        logger.debug(f"Adjusting file path from '{file_path}' to '{relative_path}' (removing project directory prefix)")
                        file_path = relative_path
                    elif file_path == project_dir:
                        logger.debug(f"Adjusting file path from '{file_path}' to root of project directory")
                        file_path = ""
                    
                    # Write file with the adjusted path
                    project_fs.write_sync(file_path, file_info['content'])
        
        logger.info(f"Created project '{name}' in directory: {full_project_dir}")
        return project_fs
    
    def get_overview(self) -> Dict[str, Any]:
        """
        Get an overview of the project for task execution.
        
        Returns a comprehensive overview of the project including metadata,
        directory structure, and task status for use in task prompts.
        
        Returns:
            Dictionary with project overview
        """
        try:
            # Get project metadata
            project_data = self.get_project()
            
            # Get directory structure
            directory_structure = {
                "src": self.list_sync("src"),
                "docs": self.list_sync("docs")
            }
            
            # Get additional directories
            for folder in project_data.get("folder_structure", []):
                if folder not in ["src", "docs"] and self.exists_sync(folder):
                    directory_structure[folder] = self.list_sync(folder)
            
            # Get tasks information
            tasks_content = ""
            if self.exists_sync("tasks.md"):
                tasks_content = self.read_sync("tasks.md")
            
            # Count completed vs total tasks
            completed_tasks = 0
            total_tasks = 0
            
            for line in tasks_content.splitlines():
                line = line.strip()
                if line.startswith("- ["):
                    total_tasks += 1
                    if line.startswith("- [x]"):
                        completed_tasks += 1
            
            # Calculate progress percentage
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Build the overview
            overview = {
                "project": {
                    "id": project_data.get("id", ""),
                    "name": project_data.get("name", ""),
                    "description": project_data.get("description", ""),
                    "created_at": project_data.get("created_at", ""),
                    "updated_at": project_data.get("updated_at", "")
                },
                "structure": directory_structure,
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "progress": round(progress, 2),
                    "content": tasks_content
                },
                "metadata": project_data.get("metadata", {})
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Failed to get project overview: {str(e)}")
            return {
                "error": f"Failed to get project overview: {str(e)}"
            }


# Function to get a ProjectFS instance for a project
def get_project_fs(project_dir: str) -> ProjectFS:
    """
    Get a ProjectFS instance for a specific project.
    
    Args:
        project_dir: Directory name of the project
        
    Returns:
        ProjectFS instance for the project
    """
    return ProjectFS(project_dir=project_dir) 