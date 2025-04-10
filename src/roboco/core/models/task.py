"""
Task Model

This module defines the Task model which serves both as a domain model and database model.
SQLModel is used to combine Pydantic validation with SQLAlchemy persistence.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, JSON, DateTime, Relationship

from roboco.utils.id_generator import generate_short_id

if TYPE_CHECKING:
    from roboco.core.models.message import Message
    from roboco.core.models.project import Project

class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"  # Added for better error handling

class Task(SQLModel, table=True):
    """
    Unified Task model for both domain logic and database persistence.
    
    This model serves as a single source of truth for task data.
    """
    # Database table name
    __tablename__ = "tasks"
    
    # Core fields
    id: str = Field(default_factory=generate_short_id, primary_key=True)
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(default=None, description="Detailed description of the task")
    status: TaskStatus = Field(default=TaskStatus.TODO, description="Current status of the task")
    
    # Relationships
    project_id: Optional[str] = Field(default=None, foreign_key="projects.id", description="Project this task belongs to")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=True)))
    completed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    
    # Metadata and extended fields
    meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON), description="Additional metadata")
    
    # Relationships (SQLModel)
    project: Optional["Project"] = Relationship(back_populates="tasks")
    messages: List["Message"] = Relationship(sa_relationship_kwargs={"primaryjoin": "Task.id==Message.task_id"})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "project_id": self.project_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "meta": self.meta
        }
            
        return result
        
    def mark_as_completed(self):
        """Mark the task as completed and set completed_at timestamp."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
    def update_timestamp(self):
        """Update the updated_at timestamp to now."""
        self.updated_at = datetime.utcnow()

# Note: API models have been moved to roboco.api.models.task
