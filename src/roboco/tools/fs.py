"""
Filesystem Tool

This module provides tools for file system operations including reading, writing, and managing files,
designed to be compatible with autogen's function calling mechanism.

"""

import os
import shutil
import glob
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, BinaryIO

from roboco.core.tool import Tool, command
from roboco.core.logger import get_logger
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.core.project_fs import FileSystem, ProjectFS
from roboco.core.config import load_config

# Initialize logger
logger = get_logger(__name__)

class FileSystemTool(Tool):
    """
    Tool for file system operations including reading and writing files.
    
    This tool provides a command-based interface for file operations that can be used with agent frameworks
    like AutoGen. It handles file operations within a specified workspace directory.
    """
    
    def __init__(self, workspace_dir: str = "workspace"):
        """Initialize the file system tool.
        
        Args:
            workspace_dir: Base directory for all file operations
        """
        self.workspace_dir = workspace_dir
        # Initialize the file system instance
        self._fs = None
        self._loop = asyncio.get_event_loop()

        super().__init__(
            name="filesystem",
            description="Tool for file system operations including reading and writing files.",
            # Enable auto-discovery of class methods
            auto_discover=True
        )
        
        logger.info(f"Initialized FileSystemTool with commands: {', '.join(self.commands.keys())}")
    
    @property
    def fs(self):
        """Get the filesystem instance, creating it if necessary."""
        if self._fs is None:
            # Create a filesystem instance directly using FileSystem
            config = load_config()
            workspace_path = os.path.join(config.workspace_root, self.workspace_dir)
            # Ensure the workspace directory exists
            os.makedirs(workspace_path, exist_ok=True)
            # Create the filesystem
            self._fs = FileSystem(workspace_path)
        return self._fs
    
    def _get_absolute_path(self, path: str) -> str:
        """Convert a relative path to an absolute path within the workspace.
        
        Args:
            path: Relative path to convert
            
        Returns:
            Absolute path within the workspace
        """
        return os.path.join(self.workspace_dir, path)
    
    @command(primary=True)
    def save_file(self, content: str, file_path: str, mode: str = "w") -> Dict[str, Any]:
        """
        Save content to a file at the specified path.
        
        Args:
            content: The content to save to the file
            file_path: The path where the file should be saved (relative to workspace)
            mode: File opening mode ('w' for write, 'a' for append)
            
        Returns:
            Dictionary with operation result info
        """
        try:
            # Use the filesystem to save the file
            if mode == 'a':
                success = self._loop.run_until_complete(self.fs.append(file_path, content))
            else:
                success = self._loop.run_until_complete(self.fs.write(file_path, content))
                
            if not success:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "Failed to write to file"
                }
            
            logger.info(f"Content saved to {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "message": f"Content successfully saved to {file_path}"
            }
        except Exception as e:
            logger.error(f"Error saving to {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    @command()
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read content from a file at the specified path.
        
        Args:
            file_path: The path of the file to read (relative to workspace)
            
        Returns:
            Dictionary with file content and operation info
        """
        try:
            # Use the filesystem to read the file
            content = self._loop.run_until_complete(self.fs.read(file_path))
            
            if content is None:
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File not found: {file_path}"
                }
            
            logger.info(f"Content read from {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "content": content
            }
        except Exception as e:
            logger.error(f"Error reading from {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    @command()
    def list_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        List contents of a directory.
        
        Args:
            directory_path: The path of the directory to list (relative to workspace)
            
        Returns:
            Dictionary with directory contents and operation info
        """
        try:
            # Use the filesystem to list directory contents
            files = self._loop.run_until_complete(self.fs.ls(directory_path))
            
            # Format the output to match the old format
            contents = []
            for item in files:
                item_path = os.path.join(str(self.fs.path), item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                contents.append({
                    "name": os.path.basename(item),
                    "type": item_type,
                    "path": item  # Keep paths relative
                })
            
            logger.info(f"Listed directory contents of {directory_path}")
            return {
                "success": True,
                "directory_path": directory_path,
                "contents": contents,
                "count": len(contents)
            }
        except Exception as e:
            logger.error(f"Error listing directory {directory_path}: {e}")
            return {
                "success": False,
                "directory_path": directory_path,
                "error": f"Error listing directory {directory_path}: {str(e)}"
            }
    
    @command()
    def create_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Create a directory at the specified path.
        
        Args:
            directory_path: The path where the directory should be created (relative to workspace)
            
        Returns:
            Dictionary with operation result info
        """
        try:
            # Use the filesystem to create the directory
            success = self._loop.run_until_complete(self.fs.mkdir(directory_path))
            
            if not success:
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": "Failed to create directory"
                }
            
            logger.info(f"Created directory at {directory_path}")
            return {
                "success": True,
                "directory_path": directory_path,
                "message": f"Directory created at {directory_path}"
            }
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return {
                "success": False,
                "directory_path": directory_path,
                "error": f"Error creating directory {directory_path}: {str(e)}"
            }
    
    @command()
    def execute_project_manifest(self, manifest: ProjectManifest, base_path: str = "") -> Dict[str, Any]:
        """Execute a project manifest to create a complete project structure.
        
        Args:
            manifest: Project manifest containing directories and files to create
            base_path: Base path for the project (relative to workspace)
            
        Returns:
            Dict containing results of the operation
        """
        try:
            # Convert dict to ProjectManifest if needed
            if isinstance(manifest, dict):
                manifest_obj = dict_to_project_manifest(manifest)
            else:
                manifest_obj = manifest
                
            # Create a ProjectManifest results structure
            results = {
                "success": True,
                "created_directories": [],
                "created_files": [],
                "errors": []
            }
            
            # Create directories
            for directory in manifest_obj.directories or []:
                dir_path = os.path.join(base_path, directory) if base_path else directory
                try:
                    mkdir_result = self.create_directory(dir_path)
                    if mkdir_result["success"]:
                        results["created_directories"].append(directory)
                    else:
                        results["errors"].append(f"Error creating directory {directory}: {mkdir_result.get('error')}")
                        results["success"] = False
                except Exception as e:
                    results["errors"].append(f"Error creating directory {directory}: {str(e)}")
                    results["success"] = False
            
            # Create files
            for file_info in manifest_obj.files or []:
                file_path = os.path.join(base_path, file_info.path) if base_path else file_info.path
                content = file_info.content
                
                # Create parent directory if it doesn't exist
                parent_dir = os.path.dirname(file_path)
                if parent_dir:
                    try:
                        mkdir_result = self.create_directory(parent_dir)
                        if not mkdir_result["success"]:
                            results["errors"].append(f"Error creating parent directory for {file_info.path}: {mkdir_result.get('error')}")
                            results["success"] = False
                            continue
                    except Exception as e:
                        results["errors"].append(f"Error creating parent directory for {file_info.path}: {str(e)}")
                        results["success"] = False
                        continue
                
                try:
                    save_result = self.save_file(content, file_path)
                    if save_result["success"]:
                        results["created_files"].append(file_info.path)
                    else:
                        results["errors"].append(f"Error creating file {file_info.path}: {save_result.get('error')}")
                        results["success"] = False
                except Exception as e:
                    results["errors"].append(f"Error creating file {file_info.path}: {str(e)}")
                    results["success"] = False
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing project manifest: {e}")
            return {
                "success": False,
                "error": f"Error executing project manifest: {str(e)}",
                "created_directories": [],
                "created_files": [],
                "errors": [str(e)]
            }