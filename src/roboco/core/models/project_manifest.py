"""
Project Manifest Domain Model

This module defines the ProjectManifest domain entity and related models,
which describe the structure and metadata of a project.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from loguru import logger

logger = logger.bind(module=__name__)

# Define Pydantic models for project manifest
class ProjectFile(BaseModel):
    """File to be created in the project."""
    path: str = Field(..., description="Path to the file within the project")
    content: str = Field(..., description="Content of the file")
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v):
        """Validate that the path is relative and doesn't contain ../ traversal."""
        if v.startswith('/'):
            raise ValueError(f"Path must be relative, not absolute: {v}")
        if '../' in v:
            raise ValueError(f"Path must not contain directory traversal: {v}")
        return v

class ProjectManifest(BaseModel):
    """Manifest describing a project structure and metadata."""
    id: str = Field(..., description="Project unique identifier")
    name: str = Field(..., description="Human-readable project name")
    description: str = Field(..., description="Project description")
    structure: Dict[str, Any] = Field(default_factory=dict, description="Project structure type")
    folder_structure: List[str] = Field(default_factory=list, description="List of top-level directories")
    files: Optional[List[ProjectFile]] = Field(default_factory=list, description="Files to create")
    
    @model_validator(mode='after')
    def validate_paths(self):
        """Validate that file and folder paths don't include project ID as prefix."""
        project_id = self.id
        if not project_id:
            return self
            
        # Check folder paths
        for folder in self.folder_structure:
            if folder.startswith(f"{project_id}/") or folder.startswith(f"{project_id}\\"):
                raise ValueError(
                    f"Folder path '{folder}' includes project ID as prefix. "
                    f"Paths must be relative to the project root without including the project ID."
                )
                
        # Check file paths
        for file_info in self.files:
            if hasattr(file_info, 'path'):
                if file_info.path.startswith(f"{project_id}/") or file_info.path.startswith(f"{project_id}\\"):
                    raise ValueError(
                        f"File path '{file_info.path}' includes project ID as prefix. "
                        f"Paths must be relative to the project root without including the project ID."
                    )
                    
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "A1c23fb",
                "name": "Todo App",
                "description": "A simple todo application",
                "structure": {"type": "dev"},
                "folder_structure": ["src", "docs", "tests"],
                "files": [
                    {
                        "path": "tasks.json",
                        "content": "{\"project_id\": \"A1c23fb\", \"tasks\": []}"
                    },
                    {
                        "path": "project.json",
                        "content": "{\"id\": \"A1c23fb\", \"name\": \"Todo App\", \"description\": \"A simple todo application\", \"created_at\": \"2023-01-01T00:00:00\"}"
                    }
                ]
            }
        }
    }

def validate_manifest(manifest: Dict[str, Any]) -> bool:
    """
    Validate a project manifest using Pydantic models.
    
    Args:
        manifest: The project manifest to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ProjectManifest(**manifest)
        return True
    except Exception:
        return False

def dict_to_project_manifest(data: Dict[str, Any]) -> ProjectManifest:
    """
    Convert a dictionary to a ProjectManifest.
    
    Args:
        data: Dictionary containing project manifest data
        
    Returns:
        ProjectManifest object
        
    Raises:
        ValueError: If the data is invalid
    """
    return ProjectManifest(**data)
