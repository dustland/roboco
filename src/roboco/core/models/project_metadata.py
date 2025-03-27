"""
Project Metadata

This module defines the ProjectMetadata class which represents the structured data
stored in project.json files.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectMetadata(BaseModel):
    """
    Represents the metadata for a project stored in project.json.
    
    This class provides a structured representation of project metadata
    and handles serialization/deserialization for project.json files.
    """
    
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    teams: List[str] = Field(default_factory=list)
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    source_code_dir: str = "src"
    docs_dir: str = "docs"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectMetadata":
        """
        Create a ProjectMetadata instance from a dictionary.
        
        Args:
            data: Dictionary representation of project metadata
            
        Returns:
            ProjectMetadata instance
        """
        # Handle date strings
        if isinstance(data.get("created_at"), str):
            data["created_at"] = data["created_at"]
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = data["updated_at"]
            
        # Handle project_dir to project_id conversion for backward compatibility
        if "project_dir" in data and "id" not in data:
            data["id"] = data.pop("project_dir")
            
        return cls(**data) 