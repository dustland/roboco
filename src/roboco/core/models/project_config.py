"""
Project Configuration Model

This module defines the schema for project configuration, used primarily for API interactions.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from roboco.core.models.task import Task


class ProjectConfig(BaseModel):
    """
    Configuration model for projects in the API layer.
    
    This model represents a project in a serializable format suitable for API responses
    and persisting to storage.
    """
    id: Optional[str] = Field(
        None,
        description="Unique identifier for the project"
    )
    name: str = Field(
        ...,
        description="Name of the project"
    )
    description: str = Field(
        ...,
        description="Description of the project"
    )
    directory: str = Field(
        ...,
        description="Path to the project directory"
    )
    teams: List[str] = Field(
        default_factory=list,
        description="Teams assigned to the project"
    )
    jobs: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Jobs associated with the project"
    )
    current_sprint: Optional[Dict[str, Any]] = Field(
        None,
        description="Currently active sprint details"
    )
    tasks: List[Task] = Field(
        default_factory=list,
        description="Tasks in the project"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorizing the project"
    )
    source_code_dir: Optional[str] = Field(
        None,
        description="Directory containing source code"
    )
    docs_dir: Optional[str] = Field(
        None,
        description="Directory containing documentation"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the project was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="When the project was last updated"
    )
    
    class Config:
        """Pydantic config for the model."""
        arbitrary_types_allowed = True 