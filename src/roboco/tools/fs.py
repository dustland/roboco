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
import traceback

from roboco.core.project_fs import ProjectFS
from roboco.core.tool import Tool, command
from loguru import logger
from roboco.core.models.project_manifest import ProjectManifest, dict_to_project_manifest

# Initialize logger
logger = logger.bind(module=__name__)

class FileSystemTool(Tool):
    """
    Tool for file system operations including reading and writing files.
    
    This tool provides a command-based interface for file operations that can be used with agent frameworks
    like AutoGen. It handles file operations within a specified workspace directory.
    """
    
    def __init__(self, fs: ProjectFS):
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
    def execute_project_manifest(self, manifest: ProjectManifest) -> Dict[str, Any]:
        """
        Execute a project manifest to create a new project.
        
        The ProjectManifest is a domain object that describes the structure of a project, 
        including its name, description, directory structure, and files. This follows
        Domain-Driven Design principles by using the domain object as the primary way to 
        create projects.
        
        Note: File paths in the manifest should be relative to the project directory,
        not prefixed with the project directory name. Any project directory prefixes 
        will be automatically removed.
        
        Args:
            manifest: Project manifest data
            
        Returns:
            Dictionary with status information
        """
        logger.info(f"Executing project manifest")
        
        try:
            # Use ProjectFS.initialize directly, avoiding circular imports
            from roboco.core.project import Project
            from roboco.core.models.project_manifest import dict_to_project_manifest
            
            # Check if we have name and description in the manifest
            if isinstance(manifest, dict) and 'name' in manifest and 'description' in manifest:
                # Create the project using ProjectFS.initialize with extracted values
                project = Project.initialize(
                    name=manifest['name'],
                    description=manifest['description'],
                    project_id=manifest.get('id'),
                    manifest=manifest
                )
            else:
                # Convert to ProjectManifest first to extract required fields
                project_manifest = dict_to_project_manifest(manifest) if isinstance(manifest, dict) else manifest
                
                # Create the project using ProjectFS.initialize with extracted values
                project = Project.initialize(
                    name=project_manifest.name,
                    description=project_manifest.description,
                    project_id=project_manifest.id,
                    manifest=project_manifest
                )
                
            # Get the project details to return
            try:
                project_data = self.fs.read_json_sync("project.json")
            except FileNotFoundError:
                raise ValueError(f"Project file not found: project.json")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in project file: project.json")
            
            # Log the project data for debugging
            logger.debug(f"Project data: {project_data}")
            
            # Access the project_id safely with a fallback
            project_id = project_data.get("id", "unknown_id")
            logger.debug(f"Project id determined to be: {project_id}")
            
            return {
                "status": "success",
                "message": f"Project manifest executed successfully",
                "project_id": project_id
            }
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Error executing project manifest: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Failed to execute project manifest: {error_msg}"
            }
        except FileNotFoundError as e:
            error_msg = f"File not found: {str(e)}"
            logger.error(f"Error executing project manifest: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Failed to execute project manifest: {error_msg}"
            }
        except PermissionError as e:
            error_msg = f"Permission denied: {str(e)}"
            logger.error(f"Error executing project manifest: {error_msg}")
            return {
                "status": "error",
                "message": f"Failed to execute project manifest: {error_msg}"
            }
        except KeyError as e:
            error_msg = f"Missing key in manifest: {str(e)}"
            logger.error(f"Error executing project manifest: {error_msg}")
            return {
                "status": "error", 
                "message": f"Failed to execute project manifest: {error_msg}"
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error executing project manifest: {error_msg}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "status": "error",
                "message": f"Failed to execute project manifest: {error_msg}"
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