"""
Project Model

This module defines the Project model which serves both as a domain model and database model.
SQLModel is used to combine Pydantic validation with SQLAlchemy persistence.
"""
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from uuid import uuid4
from sqlmodel import SQLModel, Field, Column, JSON, DateTime, Relationship

if TYPE_CHECKING:
    from roboco.core.models.task import Task

class Project(SQLModel, table=True):
    """
    Unified Project model for both domain logic and database persistence.
    
    This model serves as a single source of truth for project data.
    """
    # Database table name
    __tablename__ = "projects"
    
    # Core fields
    id: str = Field(default_factory=lambda: str(uuid4())[:8], primary_key=True)
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

# Note: API models have been moved to roboco.api.models.project 