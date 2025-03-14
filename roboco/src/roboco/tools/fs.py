"""
Filesystem Tool

This module provides tools for file system operations including reading, writing, and managing files,
designed to be compatible with autogen's function calling mechanism.
"""

import os
from typing import Dict, Any, Optional
from loguru import logger

from roboco.core.tool import Tool

class FileSystemTool(Tool):
    """Tool for file system operations including reading and writing files."""
    
    def __init__(self):
        """Initialize the file system tool."""
        super().__init__(name="fs", description="Perform file system operations")
        logger.info("Initialized FileSystemTool")
    
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
            logger.error(f"Error saving file {file_path}: {str(e)}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read content from a file at the specified path.
        
        Args:
            file_path: The path of the file to read
            
        Returns:
            Dictionary with file content and operation result info
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "file_path": file_path,
                    "error": f"File not found: {file_path}"
                }
            
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            logger.info(f"File read from {file_path}")
            return {
                "success": True,
                "file_path": file_path,
                "content": content
            }
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return {
                "success": False,
                "file_path": file_path,
                "error": str(e)
            }
    
    def list_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        List the contents of a directory.
        
        Args:
            directory_path: The path of the directory to list
            
        Returns:
            Dictionary with directory contents and operation result info
        """
        try:
            if not os.path.exists(directory_path):
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": f"Directory not found: {directory_path}"
                }
            
            if not os.path.isdir(directory_path):
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": f"Path is not a directory: {directory_path}"
                }
            
            files = []
            dirs = []
            
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    dirs.append(item)
                else:
                    files.append(item)
            
            logger.info(f"Listed directory contents for {directory_path}")
            return {
                "success": True,
                "directory_path": directory_path,
                "files": files,
                "directories": dirs,
                "total_files": len(files),
                "total_directories": len(dirs)
            }
        except Exception as e:
            logger.error(f"Error listing directory {directory_path}: {str(e)}")
            return {
                "success": False,
                "directory_path": directory_path,
                "error": str(e)
            }
    
    def create_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Create a new directory.
        
        Args:
            directory_path: The path of the directory to create
            
        Returns:
            Dictionary with operation result info
        """
        try:
            if os.path.exists(directory_path):
                if os.path.isdir(directory_path):
                    return {
                        "success": True,
                        "directory_path": directory_path,
                        "message": f"Directory already exists: {directory_path}"
                    }
                else:
                    return {
                        "success": False,
                        "directory_path": directory_path,
                        "error": f"Path exists but is not a directory: {directory_path}"
                    }
            
            os.makedirs(directory_path)
            
            logger.info(f"Created directory at {directory_path}")
            return {
                "success": True,
                "directory_path": directory_path,
                "message": f"Directory successfully created at {directory_path}"
            }
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {str(e)}")
            return {
                "success": False,
                "directory_path": directory_path,
                "error": str(e)
            }