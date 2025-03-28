"""
Project Manifest Domain Model

This module defines the ProjectManifest domain entity and related models,
which describe the structure and metadata of a project.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pydantic import BaseModel, Field

# Define Pydantic models for project manifest
class ProjectFile(BaseModel):
    """File to be created in the project."""
    path: str = Field(..., description="Path to the file within the project")
    content: str = Field(..., description="Content of the file")

class ProjectManifest(BaseModel):
    """Manifest describing a project structure and metadata."""
    id: str = Field(..., description="Project unique identifier")
    name: str = Field(..., description="Human-readable project name")
    description: str = Field(..., description="Project description")
    structure: Dict[str, Any] = Field(default_factory=dict, description="Project structure type")
    folder_structure: List[str] = Field(default_factory=list, description="List of top-level directories")
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    task_file: str = Field("tasks.md", description="Name of the task file")
    directories: Optional[List[str]] = Field(default_factory=list, description="Deprecated: use folder_structure")
    files: Optional[List[ProjectFile]] = Field(default_factory=list, description="Files to create")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "A1c23fb",
                "name": "Todo App",
                "description": "A simple todo application",
                "structure": {"type": "dev"},
                "folder_structure": ["src", "docs", "tests"],
                "meta": {
                    "teams": ["frontend", "backend"],
                },
                "files": [
                    {
                        "path": "tasks.md",
                        "content": "# Todo App\n\nA simple todo application."
                    }
                ]
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
    # Convert the files list to ProjectFile objects
    if "files" in data and data["files"] and isinstance(data["files"], list):
        data["files"] = [
            ProjectFile(**file) if isinstance(file, dict) else file
            for file in data["files"]
        ]
    
    return ProjectManifest(**data)
