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
        
        # Define the save_file function
        def save_file(content: str, file_path: str, mode: str = "w") -> Dict[str, Any]:
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
        
        # Define the read_file function
        def read_file(file_path: str) -> Dict[str, Any]:
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
        
        # Define the list_directory function
        def list_directory(directory_path: str) -> Dict[str, Any]:
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
                
                # List directory contents
                contents = os.listdir(directory_path)
                
                # Get file types
                items = []
                for item in contents:
                    item_path = os.path.join(directory_path, item)
                    item_type = "directory" if os.path.isdir(item_path) else "file"
                    items.append({
                        "name": item,
                        "type": item_type,
                        "path": item_path
                    })
                
                logger.info(f"Listed contents of {directory_path}")
                return {
                    "success": True,
                    "directory_path": directory_path,
                    "contents": items,
                    "count": len(items)
                }
            except Exception as e:
                logger.error(f"Error listing directory {directory_path}: {e}")
                return {
                    "success": False,
                    "directory_path": directory_path,
                    "error": str(e)
                }
        
        # Initialize the Tool parent class with auto-discovery enabled
        super().__init__(
            name="filesystem",
            description="Tool for file system operations including reading, writing, and listing files"
            # No need to manually register functions - they will be auto-discovered
        )
        
        # Ensure name is accessible through both parent class mechanisms
        self._name = "filesystem"
        
        logger.info(f"Initialized FileSystemTool with auto-discovered commands: {', '.join(self.commands.keys())}")