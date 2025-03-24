"""
Project Manifest Schema

This module defines the schema and validation for project manifests.
"""

from typing import Dict, Any, List, Optional
import json
from pydantic import BaseModel, Field

# Define Pydantic models for project manifest
class ProjectFile(BaseModel):
    """Model representing a file in a project manifest."""
    path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="Content of the file")

class ProjectManifest(BaseModel):
    """Model representing a complete project manifest."""
    name: str = Field(..., description="Project name in kebab-case (lowercase with hyphens)")
    directories: List[str] = Field(..., description="List of directory paths to create")
    files: List[ProjectFile] = Field(..., description="List of files to create with their content")

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
