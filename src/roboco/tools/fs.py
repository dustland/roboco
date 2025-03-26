"""
Filesystem Tool

This module provides tools for file system operations including reading, writing, and managing files,
designed to be compatible with autogen's function calling mechanism.

"""

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import concurrent.futures
import json

from roboco.core.tool import Tool, command
from roboco.core.logger import get_logger
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest
from roboco.core.project_fs import FileSystem, ProjectFS

# Initialize logger
logger = get_logger(__name__)

class FileSystemTool(Tool):
    """
    Tool for file system operations including reading and writing files.
    
    This tool provides a command-based interface for file operations that can be used with agent frameworks
    like AutoGen. It handles file operations within a specified workspace directory.
    """
    
    def __init__(self, fs: FileSystem):
        """Initialize the file system tool.
        
        FileSystem must be provided.
        
        Args:
            fs: FileSystem instance
        """
        self.fs = fs

        super().__init__(
            name="filesystem",
            description="Tool for file system operations including reading and writing files.",
            # Enable auto-discovery of class methods
            auto_discover=True
        )
        
        logger.info(f"Initialized FileSystemTool with commands: {', '.join(self.commands.keys())}")
    
    def _run_async(self, coro):
        """
        Helper method to run an async coroutine from a sync context safely.
        
        Args:
            coro: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        # Trace the coroutine before execution
        coroutine_name = getattr(coro, "__name__", "unknown")
        frame = getattr(coro, "cr_frame", None)
        args_info = ""
        
        if frame and frame.f_locals:
            args_info = f" with args: {', '.join(f'{k}={v}' for k, v in frame.f_locals.items() if k != 'self')}"
        
        logger.debug(f"Starting async operation '{coroutine_name}'{args_info}")
        
        try:
            # Try to get the currently running event loop
            loop = asyncio.get_running_loop()
            # If we're in an async context (loop is already running), use run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            # Add strict timeout to fail fast
            return future.result(timeout=5)
        except RuntimeError:
            # If no event loop is running (we're in a sync context), create a new one
            return asyncio.run(coro)
        except concurrent.futures.TimeoutError:
            logger.error(f"Operation '{coroutine_name}'{args_info} timed out after 5 seconds")
            raise TimeoutError(f"Operation '{coroutine_name}' timed out after 5 seconds")
    
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
            logger.info(f"Saving file: {file_path} (mode: {mode})")
            
            # Use filesystem's methods based on mode
            success = False
            if mode == "a":
                success = self.fs.append_sync(file_path, content)
            else:
                success = self.fs.write_sync(file_path, content)
            
            if success:
                logger.info(f"Successfully saved content to {file_path}")
                return {
                    "success": True,
                    "file_path": file_path,
                    "message": f"Content successfully saved to {file_path}"
                }
            else:
                logger.error(f"Failed to save content to {file_path}")
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"Failed to save content to {file_path}"
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
            logger.info(f"Reading file: {file_path}")
            
            # Check if file exists
            if not self.fs.exists_sync(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File not found: {file_path}"
                }
            
            # Use filesystem's read method
            try:
                content = self.fs.read_sync(file_path)
                
                logger.info(f"Successfully read content from {file_path}")
                return {
                    "success": True,
                    "file_path": file_path,
                    "content": content
                }
            except Exception as e:
                logger.error(f"Error reading file: {str(e)}")
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"Error reading file: {str(e)}"
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
            logger.info(f"Listing directory: {directory_path}")
            
            # Check if directory exists
            if not self.fs.exists_sync(directory_path) or not self.fs.is_dir_sync(directory_path):
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": f"Directory not found: {directory_path}"
                }
                
            # Use filesystem's list method
            try:
                files = self.fs.list_sync(directory_path)
                
                # Format the output
                contents = []
                for item in files:
                    item_path = os.path.join(directory_path, item)
                    item_type = "directory" if self.fs.is_dir_sync(item_path) else "file"
                    contents.append({
                        "name": item,
                        "type": item_type,
                        "path": item_path  # Keep paths relative
                    })
                
                logger.info(f"Listed {len(contents)} items in directory {directory_path}")
                return {
                    "success": True,
                    "directory_path": directory_path,
                    "contents": contents,
                    "count": len(contents)
                }
            except Exception as e:
                logger.error(f"Error listing directory contents: {str(e)}")
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": f"Error listing directory contents: {str(e)}"
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
            logger.info(f"Creating directory: {directory_path}")
            
            # Use filesystem's synchronous mkdir method
            success = self.fs.mkdir_sync(directory_path)
            
            if success:
                logger.info(f"Successfully created directory at {directory_path}")
                return {
                    "success": True,
                    "directory_path": directory_path,
                    "message": f"Directory created at {directory_path}"
                }
            else:
                logger.error(f"Failed to create directory at {directory_path}")
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": "Directory creation failed"
                }
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {e}")
            return {
                "success": False,
                "directory_path": directory_path,
                "error": f"Error creating directory {directory_path}: {str(e)}"
            }
    
    @command()
    def execute_project_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a project manifest to create directories and files.
        
        Args:
            manifest: Project manifest data
            
        Returns:
            Dictionary with status information
        """
        logger.info(f"Executing project manifest")
        
        try:
            # Convert dictionary to ProjectManifest object
            project_manifest = dict_to_project_manifest(manifest)
            
            # Use only the directory_name as the project directory without any path prefixes
            # This ensures projects are created directly in the workspace without nesting
            project_dir = project_manifest.directory_name

            # Log the current working directory and where we're creating the project
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Creating project in workspace: {self.fs.base_dir}")
            
            # Check if project directory already exists
            if self.fs.exists_sync(project_dir):
                logger.warning(f"Project directory {project_dir} already exists")
                # Let's delete this dir
                self.fs.rmdir_sync(project_dir)
                logger.info(f"Deleted existing project directory: {project_dir}")

            # Create the project directory using the synchronous filesystem method
            self.fs.mkdir_sync(project_dir)
            logger.info(f"Created project directory: {project_dir}")
            
            # Create folder structure
            for folder in project_manifest.folder_structure:
                folder_path = os.path.join(project_dir, folder)
                self.fs.mkdir_sync(folder_path)
                logger.info(f"Created folder: {folder_path}")
                
            # Create files
            if project_manifest.files:
                for file_info in project_manifest.files:
                    # Get the file path
                    file_path = file_info.path
                    
                    # Create parent directory if needed
                    parent_dir = os.path.dirname(file_path)
                    if parent_dir:
                        self.fs.mkdir_sync(parent_dir)
                    
                    # Write the file with the synchronous filesystem method
                    self.fs.write_sync(file_path, file_info.content)
                    logger.info(f"Created file: {file_path}")
            
            return {
                "status": "success",
                "message": f"Project manifest executed successfully",
                "project_dir": project_dir
            }
            
        except Exception as e:
            logger.error(f"Error executing project manifest: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to execute project manifest: {str(e)}"
            }
    
    @command()
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete a file at the specified path.
        
        Args:
            file_path: The path of the file to delete (relative to workspace)
            
        Returns:
            Dictionary with operation result info
        """
        try:
            logger.info(f"Deleting file: {file_path}")
            
            # Check if file exists
            if not self.fs.exists_sync(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File not found: {file_path}"
                }
            
            # Use filesystem's delete method
            success = self.fs.delete_sync(file_path)
            
            if success:
                logger.info(f"Successfully deleted file at {file_path}")
                return {
                    "success": True,
                    "file_path": file_path,
                    "message": f"File deleted at {file_path}"
                }
            else:
                logger.error(f"Failed to delete file at {file_path}")
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": "File deletion failed"
                }
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Error deleting file {file_path}: {str(e)}"
            }
    
    @command()
    def file_exists(self, file_path: str) -> Dict[str, Any]:
        """
        Check if a file exists at the specified path.
        
        Args:
            file_path: The path of the file to check (relative to workspace)
            
        Returns:
            Dictionary with existence info
        """
        try:
            logger.info(f"Checking if file exists: {file_path}")
            
            # Use filesystem's exists method
            exists = self.fs.exists_sync(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "exists": exists
            }
        except Exception as e:
            logger.error(f"Error checking if file exists {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Error checking if file exists {file_path}: {str(e)}"
            }
            
    @command()
    def read_json(self, file_path: str) -> Dict[str, Any]:
        """
        Read and parse a JSON file at the specified path.
        
        Args:
            file_path: The path of the JSON file to read (relative to workspace)
            
        Returns:
            Dictionary with parsed JSON content and operation info
        """
        try:
            logger.info(f"Reading JSON file: {file_path}")
            
            # Check if file exists
            if not self.fs.exists_sync(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File not found: {file_path}"
                }
            
            # Use filesystem's read method
            try:
                content = self.fs.read_sync(file_path)
                
                # Parse the JSON content
                try:
                    json_data = json.loads(content)
                    
                    logger.info(f"Successfully read and parsed JSON from {file_path}")
                    return {
                        "success": True,
                        "file_path": file_path,
                        "data": json_data
                    }
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON: {str(e)}")
                    return {
                        "success": False,
                        "file_path": file_path,
                        "error": f"Invalid JSON format: {str(e)}",
                        "content": content  # Include the raw content for debugging
                    }
                
            except Exception as e:
                logger.error(f"Error reading file: {str(e)}")
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"Error reading file: {str(e)}"
                }
        except Exception as e:
            logger.error(f"Error reading JSON from {file_path}: {e}")
            return {
                "success": False,
                "file_path": file_path,
                "error": f"Error reading JSON from {file_path}: {str(e)}"
            }