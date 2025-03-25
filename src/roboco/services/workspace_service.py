"""
Workspace Service

This module provides services for managing workspaces, including workspace creation,
file operations, and artifact management.
"""

import os
import shutil
import json
from typing import Dict, Any, List, Optional, Union, BinaryIO
from pathlib import Path
from datetime import datetime
import uuid
from loguru import logger


class WorkspaceService:
    """
    Service for managing workspaces and workspace-related operations.
    
    This service follows the DDD principles by encapsulating workspace-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self, workspace_base: Optional[str] = None):
        """
        Initialize the workspace service with its dependencies.
        
        Args:
            workspace_base: Base directory for workspaces, defaults to ~/roboco_workspace
        """
        self.workspace_base = workspace_base or os.path.expanduser("~/roboco_workspace")
        self._ensure_directory(self.workspace_base)
    
    def _ensure_directory(self, directory_path: str) -> None:
        """
        Ensure a directory exists.
        
        Centralizes directory creation to avoid scattered os.makedirs calls.
        
        Args:
            directory_path: Path to ensure exists
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.debug(f"Created directory: {directory_path}")
    
    async def create_workspace(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new workspace.
        
        Args:
            name: Name of the workspace
            description: Optional description
            
        Returns:
            Dictionary with workspace information
            
        Raises:
            ValueError: If a workspace with the same name already exists
        """
        # Create a sanitized directory name
        dir_name = name.lower().replace(" ", "_")
        workspace_path = os.path.join(self.workspace_base, dir_name)
        
        # Check if workspace already exists
        if os.path.exists(workspace_path):
            raise ValueError(f"Workspace '{name}' already exists")
        
        # Create workspace directory
        self._ensure_directory(workspace_path)
        
        # Create subdirectories
        self._ensure_directory(os.path.join(workspace_path, "artifacts"))
        self._ensure_directory(os.path.join(workspace_path, "data"))
        self._ensure_directory(os.path.join(workspace_path, "code"))
        self._ensure_directory(os.path.join(workspace_path, "docs"))
        
        # Create metadata file
        metadata = {
            "name": name,
            "description": description or "",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "id": str(uuid.uuid4())
        }
        
        with open(os.path.join(workspace_path, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "id": metadata["id"],
            "name": name,
            "description": description or "",
            "path": workspace_path,
            "created_at": metadata["created_at"]
        }
    
    async def get_workspace(self, workspace_id_or_name: str) -> Dict[str, Any]:
        """
        Get workspace information by ID or name.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            
        Returns:
            Dictionary with workspace information
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Try to find by name first (convert to directory name)
        dir_name = workspace_id_or_name.lower().replace(" ", "_")
        workspace_path = os.path.join(self.workspace_base, dir_name)
        
        # If not found by name, try to find by ID
        if not os.path.exists(workspace_path):
            # Search all workspaces for matching ID
            for ws_dir in os.listdir(self.workspace_base):
                ws_path = os.path.join(self.workspace_base, ws_dir)
                if os.path.isdir(ws_path):
                    metadata_path = os.path.join(ws_path, "metadata.json")
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                                if metadata.get("id") == workspace_id_or_name:
                                    workspace_path = ws_path
                                    break
                        except Exception as e:
                            logger.error(f"Error reading metadata for workspace {ws_dir}: {str(e)}")
        
        # Check if workspace exists
        if not os.path.exists(workspace_path):
            raise ValueError(f"Workspace '{workspace_id_or_name}' not found")
        
        # Read metadata
        metadata_path = os.path.join(workspace_path, "metadata.json")
        if not os.path.exists(metadata_path):
            # Create metadata if it doesn't exist
            metadata = {
                "name": os.path.basename(workspace_path),
                "description": "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "id": str(uuid.uuid4())
            }
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        else:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
        
        return {
            "id": metadata.get("id", str(uuid.uuid4())),
            "name": metadata.get("name", os.path.basename(workspace_path)),
            "description": metadata.get("description", ""),
            "path": workspace_path,
            "created_at": metadata.get("created_at", datetime.now().isoformat()),
            "updated_at": metadata.get("updated_at", datetime.now().isoformat())
        }
    
    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all workspaces.
        
        Returns:
            List of dictionaries with workspace information
        """
        workspaces = []
        
        for ws_dir in os.listdir(self.workspace_base):
            ws_path = os.path.join(self.workspace_base, ws_dir)
            if os.path.isdir(ws_path):
                try:
                    # Read metadata
                    metadata_path = os.path.join(ws_path, "metadata.json")
                    if os.path.exists(metadata_path):
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                    else:
                        # Create default metadata
                        metadata = {
                            "name": ws_dir,
                            "description": "",
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                            "id": str(uuid.uuid4())
                        }
                        with open(metadata_path, "w") as f:
                            json.dump(metadata, f, indent=2)
                    
                    workspaces.append({
                        "id": metadata.get("id", str(uuid.uuid4())),
                        "name": metadata.get("name", ws_dir),
                        "description": metadata.get("description", ""),
                        "path": ws_path,
                        "created_at": metadata.get("created_at", datetime.now().isoformat()),
                        "updated_at": metadata.get("updated_at", datetime.now().isoformat())
                    })
                except Exception as e:
                    logger.error(f"Error reading workspace {ws_dir}: {str(e)}")
        
        return workspaces
    
    async def update_workspace(self, workspace_id_or_name: str, 
                              name: Optional[str] = None,
                              description: Optional[str] = None) -> Dict[str, Any]:
        """
        Update workspace information.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            name: New name for the workspace
            description: New description for the workspace
            
        Returns:
            Dictionary with updated workspace information
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Get current workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Update metadata
        metadata_path = os.path.join(workspace["path"], "metadata.json")
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        if name is not None:
            metadata["name"] = name
        
        if description is not None:
            metadata["description"] = description
        
        metadata["updated_at"] = datetime.now().isoformat()
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Return updated workspace info
        return {
            "id": metadata["id"],
            "name": metadata["name"],
            "description": metadata["description"],
            "path": workspace["path"],
            "created_at": metadata["created_at"],
            "updated_at": metadata["updated_at"]
        }
    
    async def delete_workspace(self, workspace_id_or_name: str) -> bool:
        """
        Delete a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            
        Returns:
            True if the workspace was deleted, False otherwise
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Get workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Delete workspace directory
        try:
            shutil.rmtree(workspace["path"])
            return True
        except Exception as e:
            logger.error(f"Error deleting workspace: {str(e)}")
            return False
    
    async def list_files(self, workspace_id_or_name: str, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            path: Optional path within the workspace
            
        Returns:
            List of dictionaries with file information
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Get workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Determine the directory to list
        if path:
            # Ensure path doesn't try to escape the workspace
            norm_path = os.path.normpath(path)
            if norm_path.startswith("..") or norm_path.startswith("/"):
                raise ValueError(f"Invalid path: {path}")
            
            dir_path = os.path.join(workspace["path"], norm_path)
        else:
            dir_path = workspace["path"]
        
        # Check if directory exists
        if not os.path.exists(dir_path) or not os.path.isdir(dir_path):
            raise ValueError(f"Directory not found: {path or '/'}")
        
        # List files and directories
        items = []
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            rel_path = os.path.relpath(item_path, workspace["path"])
            
            # Get file stats
            stats = os.stat(item_path)
            
            items.append({
                "name": item,
                "path": rel_path,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
            })
        
        return items
    
    async def read_file(self, workspace_id_or_name: str, path: str) -> str:
        """
        Read a file from a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            path: Path to the file within the workspace
            
        Returns:
            File contents as a string
            
        Raises:
            ValueError: If the workspace or file is not found
        """
        # Get workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Ensure path doesn't try to escape the workspace
        norm_path = os.path.normpath(path)
        if norm_path.startswith("..") or norm_path.startswith("/"):
            raise ValueError(f"Invalid path: {path}")
        
        file_path = os.path.join(workspace["path"], norm_path)
        
        # Check if file exists
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            raise ValueError(f"File not found: {path}")
        
        # Read file
        try:
            with open(file_path, "r") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try to read as binary and convert to base64
            import base64
            with open(file_path, "rb") as f:
                content = f.read()
                return base64.b64encode(content).decode("utf-8")
    
    async def write_file(self, workspace_id_or_name: str, path: str, content: Union[str, bytes]) -> Dict[str, Any]:
        """
        Write content to a file in a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            path: Path to the file within the workspace
            content: Content to write (string or bytes)
            
        Returns:
            Dictionary with file information
            
        Raises:
            ValueError: If the workspace is not found or path is invalid
        """
        # Get workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Ensure path doesn't try to escape the workspace
        norm_path = os.path.normpath(path)
        if norm_path.startswith("..") or norm_path.startswith("/"):
            raise ValueError(f"Invalid path: {path}")
        
        file_path = os.path.join(workspace["path"], norm_path)
        
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        self._ensure_directory(parent_dir)
        
        # Write file
        try:
            if isinstance(content, str):
                with open(file_path, "w") as f:
                    f.write(content)
            else:
                with open(file_path, "wb") as f:
                    f.write(content)
                    
            # Get file stats
            stats = os.stat(file_path)
            
            return {
                "name": os.path.basename(file_path),
                "path": path,
                "type": "file",
                "size": stats.st_size,
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
            }
        except Exception as e:
            logger.error(f"Error writing file: {str(e)}")
            raise ValueError(f"Error writing file: {str(e)}")
    
    async def delete_file(self, workspace_id_or_name: str, path: str) -> bool:
        """
        Delete a file from a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            path: Path to the file within the workspace
            
        Returns:
            True if the file was deleted, False otherwise
            
        Raises:
            ValueError: If the workspace or file is not found
        """
        # Get workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Ensure path doesn't try to escape the workspace
        norm_path = os.path.normpath(path)
        if norm_path.startswith("..") or norm_path.startswith("/"):
            raise ValueError(f"Invalid path: {path}")
        
        file_path = os.path.join(workspace["path"], norm_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {path}")
        
        # Delete file or directory
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
