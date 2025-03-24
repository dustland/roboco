"""
Filesystem Tool

This module provides tools for file system operations including reading, writing, and managing files,
designed to be compatible with autogen's function calling mechanism.
"""

import os
from typing import Dict, Any, Union
from loguru import logger

from roboco.core.tool import Tool, command
from roboco.domain.models.project_manifest import ProjectManifest, dict_to_project_manifest

class FileSystemTool(Tool):
    """Tool for file system operations including reading and writing files."""
    
    def __init__(self):
        """Initialize the file system tool."""
        super().__init__(
            name="filesystem",
            description="Tool for file system operations including reading and writing files.",
            # Enable auto-discovery of class methods
            auto_discover=True
        )
        
        logger.info(f"Initialized FileSystemTool with commands: {', '.join(self.commands.keys())}")
    
    @command(primary=True)
    def save_file(self, content: str, file_path: str, mode: str = "w") -> Dict[str, Any]:
        """
        Save content to a file at the specified path.
        
        Args:
            content: The content to save to the file
            file_path: The path where the file should be saved
            mode: File opening mode ('w' for write, 'a' for append)
            
        Returns:
            Dictionary with operation result info
        """
        try:
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Write to the file
            with open(file_path, mode, encoding="utf-8") as file:
                file.write(content)
            
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
            file_path: The path of the file to read
            
        Returns:
            Dictionary with file content and operation info
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File not found: {file_path}"
                }
            
            # Read the file
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            
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
            directory_path: The path of the directory to list
            
        Returns:
            Dictionary with directory contents and operation info
        """
        try:
            # Check if directory exists
            if not os.path.exists(directory_path):
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": f"Directory not found: {directory_path}"
                }
            
            # Check if path is a directory
            if not os.path.isdir(directory_path):
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": f"Path is not a directory: {directory_path}"
                }
            
            # List contents
            contents = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                item_type = "directory" if os.path.isdir(item_path) else "file"
                contents.append({
                    "name": item,
                    "type": item_type,
                    "path": item_path
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
            directory_path: The path where the directory should be created
            
        Returns:
            Dictionary with operation result info
        """
        try:
            # Check if directory already exists
            if os.path.exists(directory_path):
                return {
                    "success": True,
                    "directory_path": directory_path,
                    "message": f"Directory already exists: {directory_path}"
                }
            
            # Create the directory
            os.makedirs(directory_path, exist_ok=True)
            
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
    def execute_project_manifest(self, manifest: Union[Dict[str, Any], ProjectManifest], base_path: str) -> Dict[str, Any]:
        """Execute a project manifest to create a complete project structure.
        
        Args:
            manifest: Project manifest containing directories and files to create
            base_path: Base path for the project
            
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
            for directory in manifest.directories:
                dir_path = os.path.join(base_path, directory)
                try:
                    self.create_directory(dir_path)
                    results["created_directories"].append(directory)
                except Exception as e:
                    results["errors"].append(f"Error creating directory {directory}: {str(e)}")
                    results["success"] = False
            
            # Create files
            for file_info in manifest.files:
                file_path = os.path.join(base_path, file_info.path)
                content = file_info.content
                
                # Create parent directory if it doesn't exist
                parent_dir = os.path.dirname(file_path)
                if parent_dir and not os.path.exists(parent_dir):
                    try:
                        self.create_directory(parent_dir)
                        if parent_dir.replace(base_path, "").strip("/"):  # Only add if not the base path
                            relative_dir = os.path.relpath(parent_dir, base_path)
                            if relative_dir not in results["created_directories"]:
                                results["created_directories"].append(relative_dir)
                    except Exception as e:
                        results["errors"].append(f"Error creating parent directory for {file_info.path}: {str(e)}")
                        results["success"] = False
                        continue
                
                try:
                    self.save_file(content, file_path)
                    results["created_files"].append(file_info.path)
                except Exception as e:
                    results["errors"].append(f"Error creating file {file_info.path}: {str(e)}")
                    results["success"] = False
        
        except Exception as e:
            results["errors"].append(f"Error executing project manifest: {str(e)}")
            results["success"] = False
        
        return results