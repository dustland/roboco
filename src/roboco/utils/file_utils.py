"""
File Operations Utilities

This module provides centralized utility functions for file and directory operations.
All direct file I/O operations in the codebase should use these utilities instead of
direct open(), write(), read() calls.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Union, BinaryIO, TextIO, Dict, Any
import json
import yaml
from datetime import datetime
from loguru import logger


def ensure_directory(directory_path: Union[str, Path]) -> bool:
    """
    Ensures a directory exists, creating it if it doesn't.
    
    Args:
        directory_path: Path to the directory to ensure exists
        
    Returns:
        bool: True if the directory exists or was created successfully, False otherwise
    """
    try:
        path = Path(directory_path)
        
        # If the directory already exists, return early
        if path.exists() and path.is_dir():
            logger.debug(f"Directory already exists: {path}")
            return True
        
        # Create the directory and any parent directories
        path.mkdir(parents=True, exist_ok=True)
        
        # Verify creation was successful
        if path.exists() and path.is_dir():
            logger.debug(f"Created directory: {path}")
            return True
        else:
            logger.error(f"Failed to create directory: {path}")
            return False
            
    except PermissionError as e:
        logger.error(f"Permission error creating directory {directory_path}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error creating directory {directory_path}: {str(e)}")
        return False


async def read_file(file_path: Union[str, Path], binary: bool = False) -> Optional[Union[str, bytes]]:
    """
    Read file contents with error handling.
    
    Args:
        file_path: Path to the file to read
        binary: Whether to read in binary mode
        
    Returns:
        File contents as string or bytes, or None if read failed
    """
    try:
        mode = "rb" if binary else "r"
        with open(file_path, mode) as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}")
        return None
    except PermissionError:
        logger.error(f"Permission denied when reading file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return None


async def write_file(file_path: Union[str, Path], content: Union[str, bytes], binary: bool = False) -> bool:
    """
    Write content to a file with error handling.
    
    Args:
        file_path: Path to the file to write
        content: Content to write
        binary: Whether to write in binary mode
        
    Returns:
        True if write was successful, False otherwise
    """
    try:
        # Ensure the parent directory exists
        ensure_directory(os.path.dirname(file_path))
        
        # Write the file
        mode = "wb" if binary else "w"
        with open(file_path, mode) as f:
            f.write(content)
        
        logger.debug(f"Successfully wrote file: {file_path}")
        return True
    except PermissionError:
        logger.error(f"Permission denied when writing file: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {str(e)}")
        return False


async def append_to_file(file_path: Union[str, Path], content: Union[str, bytes], binary: bool = False) -> bool:
    """
    Append content to a file with error handling.
    
    Args:
        file_path: Path to the file to append to
        content: Content to append
        binary: Whether to append in binary mode
        
    Returns:
        True if append was successful, False otherwise
    """
    try:
        # Ensure the parent directory exists
        ensure_directory(os.path.dirname(file_path))
        
        # Append to the file
        mode = "ab" if binary else "a"
        with open(file_path, mode) as f:
            f.write(content)
        
        logger.debug(f"Successfully appended to file: {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error appending to file {file_path}: {str(e)}")
        return False


async def delete_file(file_path: Union[str, Path]) -> bool:
    """
    Delete a file with error handling.
    
    Args:
        file_path: Path to the file to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            logger.debug(f"Successfully deleted: {file_path}")
            return True
        logger.warning(f"File does not exist, cannot delete: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {str(e)}")
        return False


async def list_files(directory_path: Union[str, Path], pattern: Optional[str] = None) -> List[str]:
    """
    List files in a directory with optional pattern matching.
    
    Args:
        directory_path: Path to the directory to list
        pattern: Optional glob pattern to filter files
        
    Returns:
        List of file paths matching the pattern
    """
    try:
        path = Path(directory_path)
        if not path.exists() or not path.is_dir():
            logger.warning(f"Directory does not exist: {directory_path}")
            return []
            
        if pattern:
            return [str(f) for f in path.glob(pattern)]
        else:
            return [str(f) for f in path.iterdir()]
    except Exception as e:
        logger.error(f"Error listing files in {directory_path}: {str(e)}")
        return []


async def read_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data as dictionary or None if failed
    """
    content = await read_file(file_path)
    if content is None:
        return None
        
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON from {file_path}: {str(e)}")
        return None


async def write_json_file(file_path: Union[str, Path], data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Write data to a JSON file.
    
    Args:
        file_path: Path to the JSON file
        data: Data to write as JSON
        indent: Indentation level for JSON formatting
        
    Returns:
        True if successful, False otherwise
    """
    try:
        json_content = json.dumps(data, indent=indent, default=str)
        return await write_file(file_path, json_content)
    except Exception as e:
        logger.error(f"Error writing JSON to {file_path}: {str(e)}")
        return False


async def read_yaml_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Read and parse a YAML file.
    
    Args:
        file_path: Path to the YAML file
        
    Returns:
        Parsed YAML data as dictionary or None if failed
    """
    content = await read_file(file_path)
    if content is None:
        return None
        
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML from {file_path}: {str(e)}")
        return None


async def write_yaml_file(file_path: Union[str, Path], data: Dict[str, Any]) -> bool:
    """
    Write data to a YAML file.
    
    Args:
        file_path: Path to the YAML file
        data: Data to write as YAML
        
    Returns:
        True if successful, False otherwise
    """
    try:
        yaml_content = yaml.dump(data, default_flow_style=False)
        return await write_file(file_path, yaml_content)
    except Exception as e:
        logger.error(f"Error writing YAML to {file_path}: {str(e)}")
        return False


async def copy_file(source_path: Union[str, Path], target_path: Union[str, Path]) -> bool:
    """
    Copy a file from source to target.
    
    Args:
        source_path: Path to the source file
        target_path: Path to the target file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure target directory exists
        ensure_directory(os.path.dirname(target_path))
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        logger.debug(f"Successfully copied {source_path} to {target_path}")
        return True
    except Exception as e:
        logger.error(f"Error copying {source_path} to {target_path}: {str(e)}")
        return False


async def move_file(source_path: Union[str, Path], target_path: Union[str, Path]) -> bool:
    """
    Move a file from source to target.
    
    Args:
        source_path: Path to the source file
        target_path: Path to the target file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure target directory exists
        ensure_directory(os.path.dirname(target_path))
        
        # Move the file
        shutil.move(source_path, target_path)
        logger.debug(f"Successfully moved {source_path} to {target_path}")
        return True
    except Exception as e:
        logger.error(f"Error moving {source_path} to {target_path}: {str(e)}")
        return False


def get_file_info(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Get information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information or None if file does not exist
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
            
        stats = path.stat()
        return {
            "name": path.name,
            "path": str(path),
            "size": stats.st_size,
            "is_dir": path.is_dir(),
            "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "extension": path.suffix[1:] if path.suffix else "",
        }
    except Exception as e:
        logger.error(f"Error getting file info for {file_path}: {str(e)}")
        return None 