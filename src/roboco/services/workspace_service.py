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
        os.makedirs(self.workspace_base, exist_ok=True)
    
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
        os.makedirs(workspace_path, exist_ok=True)
        
        # Create subdirectories
        os.makedirs(os.path.join(workspace_path, "artifacts"), exist_ok=True)
        os.makedirs(os.path.join(workspace_path, "data"), exist_ok=True)
        os.makedirs(os.path.join(workspace_path, "code"), exist_ok=True)
        os.makedirs(os.path.join(workspace_path, "docs"), exist_ok=True)
        
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
            name: Optional new name
            description: Optional new description
            
        Returns:
            Dictionary with updated workspace information
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Get the workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Update metadata
        metadata_path = os.path.join(workspace["path"], "metadata.json")
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        if name:
            metadata["name"] = name
        
        if description:
            metadata["description"] = description
        
        metadata["updated_at"] = datetime.now().isoformat()
        
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # If name changed, rename the directory
        if name and name.lower().replace(" ", "_") != os.path.basename(workspace["path"]):
            new_path = os.path.join(self.workspace_base, name.lower().replace(" ", "_"))
            shutil.move(workspace["path"], new_path)
            workspace["path"] = new_path
        
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
        try:
            # Get the workspace
            workspace = await self.get_workspace(workspace_id_or_name)
            
            # Delete the workspace directory
            shutil.rmtree(workspace["path"])
            
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting workspace {workspace_id_or_name}: {str(e)}")
            return False
    
    async def save_artifact(self, workspace_id_or_name: str, 
                           artifact_name: str, 
                           content: Union[str, bytes, BinaryIO],
                           artifact_type: str = "text",
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save an artifact to a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_name: Name of the artifact
            content: Content of the artifact (string, bytes, or file-like object)
            artifact_type: Type of the artifact (text, binary, image, etc.)
            metadata: Optional metadata for the artifact
            
        Returns:
            Dictionary with artifact information
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Get the workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Create artifacts directory if it doesn't exist
        artifacts_dir = os.path.join(workspace["path"], "artifacts")
        os.makedirs(artifacts_dir, exist_ok=True)
        
        # Generate a unique filename
        artifact_id = str(uuid.uuid4())
        file_ext = os.path.splitext(artifact_name)[1] if "." in artifact_name else ""
        if not file_ext:
            if artifact_type == "text":
                file_ext = ".txt"
            elif artifact_type == "json":
                file_ext = ".json"
            elif artifact_type == "image":
                file_ext = ".png"
            elif artifact_type == "html":
                file_ext = ".html"
        
        filename = f"{artifact_id}{file_ext}"
        file_path = os.path.join(artifacts_dir, filename)
        
        # Save the content
        if isinstance(content, str):
            with open(file_path, "w") as f:
                f.write(content)
        elif isinstance(content, bytes):
            with open(file_path, "wb") as f:
                f.write(content)
        else:  # File-like object
            with open(file_path, "wb") as f:
                shutil.copyfileobj(content, f)
        
        # Create metadata
        artifact_metadata = {
            "id": artifact_id,
            "name": artifact_name,
            "type": artifact_type,
            "created_at": datetime.now().isoformat(),
            "filename": filename,
            "workspace_id": workspace["id"],
            "user_metadata": metadata or {}
        }
        
        # Save metadata
        metadata_dir = os.path.join(artifacts_dir, "metadata")
        os.makedirs(metadata_dir, exist_ok=True)
        with open(os.path.join(metadata_dir, f"{artifact_id}.json"), "w") as f:
            json.dump(artifact_metadata, f, indent=2)
        
        return {
            "id": artifact_id,
            "name": artifact_name,
            "type": artifact_type,
            "path": file_path,
            "url": f"/artifacts/{workspace['id']}/{filename}",
            "created_at": artifact_metadata["created_at"],
            "metadata": metadata or {}
        }
    
    async def get_artifact(self, workspace_id_or_name: str, artifact_id_or_name: str) -> Dict[str, Any]:
        """
        Get an artifact from a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_id_or_name: ID or name of the artifact
            
        Returns:
            Dictionary with artifact information and content
            
        Raises:
            ValueError: If the workspace or artifact is not found
        """
        # Get the workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Look for the artifact
        artifacts_dir = os.path.join(workspace["path"], "artifacts")
        metadata_dir = os.path.join(artifacts_dir, "metadata")
        
        # Try to find by ID first
        if os.path.exists(metadata_dir):
            metadata_path = os.path.join(metadata_dir, f"{artifact_id_or_name}.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                
                file_path = os.path.join(artifacts_dir, metadata["filename"])
                if os.path.exists(file_path):
                    # Read content based on type
                    if metadata["type"] == "text" or metadata["type"] == "json" or metadata["type"] == "html":
                        with open(file_path, "r") as f:
                            content = f.read()
                    else:
                        with open(file_path, "rb") as f:
                            content = f.read()
                    
                    return {
                        "id": metadata["id"],
                        "name": metadata["name"],
                        "type": metadata["type"],
                        "path": file_path,
                        "url": f"/artifacts/{workspace['id']}/{metadata['filename']}",
                        "created_at": metadata["created_at"],
                        "content": content,
                        "metadata": metadata.get("user_metadata", {})
                    }
        
        # If not found by ID, try to find by name
        for root, _, files in os.walk(metadata_dir):
            for file in files:
                if file.endswith(".json"):
                    metadata_path = os.path.join(root, file)
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                        
                        if metadata["name"] == artifact_id_or_name:
                            file_path = os.path.join(artifacts_dir, metadata["filename"])
                            if os.path.exists(file_path):
                                # Read content based on type
                                if metadata["type"] == "text" or metadata["type"] == "json" or metadata["type"] == "html":
                                    with open(file_path, "r") as f:
                                        content = f.read()
                                else:
                                    with open(file_path, "rb") as f:
                                        content = f.read()
                                
                                return {
                                    "id": metadata["id"],
                                    "name": metadata["name"],
                                    "type": metadata["type"],
                                    "path": file_path,
                                    "url": f"/artifacts/{workspace['id']}/{metadata['filename']}",
                                    "created_at": metadata["created_at"],
                                    "content": content,
                                    "metadata": metadata.get("user_metadata", {})
                                }
                    except Exception as e:
                        logger.error(f"Error reading artifact metadata {file}: {str(e)}")
        
        raise ValueError(f"Artifact '{artifact_id_or_name}' not found in workspace '{workspace_id_or_name}'")
    
    async def list_artifacts(self, workspace_id_or_name: str, 
                            artifact_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all artifacts in a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_type: Optional type to filter by
            
        Returns:
            List of dictionaries with artifact information
            
        Raises:
            ValueError: If the workspace is not found
        """
        # Get the workspace
        workspace = await self.get_workspace(workspace_id_or_name)
        
        # Look for artifacts
        artifacts = []
        artifacts_dir = os.path.join(workspace["path"], "artifacts")
        metadata_dir = os.path.join(artifacts_dir, "metadata")
        
        if os.path.exists(metadata_dir):
            for root, _, files in os.walk(metadata_dir):
                for file in files:
                    if file.endswith(".json"):
                        metadata_path = os.path.join(root, file)
                        try:
                            with open(metadata_path, "r") as f:
                                metadata = json.load(f)
                            
                            # Apply type filter if specified
                            if artifact_type and metadata["type"] != artifact_type:
                                continue
                            
                            file_path = os.path.join(artifacts_dir, metadata["filename"])
                            if os.path.exists(file_path):
                                artifacts.append({
                                    "id": metadata["id"],
                                    "name": metadata["name"],
                                    "type": metadata["type"],
                                    "path": file_path,
                                    "url": f"/artifacts/{workspace['id']}/{metadata['filename']}",
                                    "created_at": metadata["created_at"],
                                    "metadata": metadata.get("user_metadata", {})
                                })
                        except Exception as e:
                            logger.error(f"Error reading artifact metadata {file}: {str(e)}")
        
        return artifacts
    
    async def delete_artifact(self, workspace_id_or_name: str, artifact_id_or_name: str) -> bool:
        """
        Delete an artifact from a workspace.
        
        Args:
            workspace_id_or_name: ID or name of the workspace
            artifact_id_or_name: ID or name of the artifact
            
        Returns:
            True if the artifact was deleted, False otherwise
            
        Raises:
            ValueError: If the workspace is not found
        """
        try:
            # Get the artifact (this will also validate the workspace)
            artifact = await self.get_artifact(workspace_id_or_name, artifact_id_or_name)
            
            # Delete the artifact file
            if os.path.exists(artifact["path"]):
                os.remove(artifact["path"])
            
            # Delete the metadata file
            workspace = await self.get_workspace(workspace_id_or_name)
            metadata_path = os.path.join(workspace["path"], "artifacts", "metadata", f"{artifact['id']}.json")
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            return True
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error deleting artifact {artifact_id_or_name}: {str(e)}")
            return False
