"""
Project Model

This module defines the Project model which serves both as a domain model and database model.
SQLModel is used to combine Pydantic validation with SQLAlchemy persistence.
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, DateTime, Relationship

from roboco.utils.id_generator import generate_short_id

if TYPE_CHECKING:
    from roboco.core.models.task import Task

class Project(SQLModel, table=True):
    """
    Unified Project model for both domain logic and database persistence.
    
    This model serves as a single source of truth for project data.
    
    Usage:
    - For creating new projects: Use with required fields, ID will be generated if not provided
    - For updating projects: Instantiate with project ID and only the fields to update
    - For database operations: Use complete model instance
    """
    # Database table name
    __tablename__ = "projects"
    
    # Core fields
    id: str = Field(default_factory=generate_short_id, primary_key=True)
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(default=None, description="Detailed description of the project")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    
    # Metadata
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="Additional metadata")
    
    # Relationships
    tasks: List["Task"] = Relationship(back_populates="project")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "meta": self.meta
        }
    
    def update_timestamp(self):
        """Update the updated_at timestamp to now."""
        self.updated_at = datetime.utcnow()

    @classmethod
    def create(cls, **kwargs) -> "Project":
        """Factory method for creating a new project.
        
        This is a convenience method for creating a new project with default values.
        
        Args:
            **kwargs: Project attributes (name is required)
            
        Returns:
            A new Project instance
        """
        # id will be auto-generated if not provided
        return cls(**kwargs)
        
    @classmethod
    def update_from_dict(cls, project_id: str, update_data: Dict[str, Any]) -> "Project":
        """Create a partial Project instance for updates.
        
        This is a convenience method for creating a Project with only fields that need updating.
        
        Args:
            project_id: ID of the project to update
            update_data: Dictionary of fields to update
            
        Returns:
            A partial Project instance with only the fields to update
        """
        # Always include the ID for the update operation
        update_data["id"] = project_id
        return cls(**update_data)

# Note: API-specific models should be defined in the API layer 