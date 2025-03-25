"""
Project Manifest Schema

This module defines the schema and validation for project manifests.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pydantic import BaseModel, Field

# Define Pydantic models for project manifest
class ProjectFile(BaseModel):
    """Model representing a file in a project manifest."""
    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content of the file")

class ProjectManifest(BaseModel):
    """Project manifest schema defining key project organization"""
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Description of the project")
    directory_name: str = Field(..., description="Clean, normalized folder name (snake_case)")
    structure: Dict[str, Any] = Field(..., description="Object describing the project's structure")
    folder_structure: List[str] = Field(default=["src", "docs"], description="Subdirectories to create")
    meta: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the project")
    created_at: datetime = Field(default_factory=datetime.now, description="When the manifest was created")
    task_file: str = Field(default="tasks.md", description="Name of the task file")
    directories: Optional[List[str]] = Field(None, description="List of directory paths to create (legacy support)")
    files: Optional[List[ProjectFile]] = Field(None, description="List of files to create (legacy support)")
    
    class Config:
        arbitrary_types_allowed = True

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

def dict_to_project_manifest(manifest_dict: Dict[str, Any]) -> ProjectManifest:
    """
    Convert a dictionary to a ProjectManifest object.
    
    Args:
        manifest_dict: Dictionary containing project manifest data
        
    Returns:
        ProjectManifest object
    """
    return ProjectManifest(**manifest_dict)
