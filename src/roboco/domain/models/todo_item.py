"""
TodoItem Domain Model

This module defines the TodoItem domain entity and related value objects.
It encapsulates the business logic for task management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from loguru import logger


class TodoItem:
    """TodoItem domain entity.
    
    This class represents a todo item or task in a project, encapsulating
    business logic for task management operations.
    """
    
    def __init__(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = "TODO",
        assigned_to: Optional[str] = None,
        priority: str = "medium",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        depends_on: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        **extra_fields
    ):
        """Initialize a TodoItem domain entity.
        
        Args:
            title: Title of the task
            description: Detailed description of the task
            status: Status of the task (TODO, IN_PROGRESS, DONE)
            assigned_to: Agent or person assigned to the task
            priority: Priority level (low, medium, high, critical)
            created_at: When the task was created
            updated_at: When the task was last updated
            completed_at: When the task was completed
            depends_on: IDs of tasks this task depends on
            tags: Tags for categorizing the task
            id: Unique identifier for the task (generated if not provided)
            **extra_fields: Additional task-specific fields
        """
        self.id = id or str(uuid.uuid4())
        self.title = title
        self.description = description
        self.status = status
        self.assigned_to = assigned_to
        self.priority = priority
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.completed_at = completed_at
        self.depends_on = depends_on or []
        self.tags = tags or []
        
        # Store any extra fields
        for key, value in extra_fields.items():
            setattr(self, key, value)
    
    def assign(self, assignee: str) -> None:
        """Assign the task to someone.
        
        Args:
            assignee: Name of the agent or person to assign the task to
        """
        self.assigned_to = assignee
        self.updated_at = datetime.now()
    
    def start(self) -> None:
        """Start working on the task.
        
        Raises:
            ValueError: If the task is already in progress or done
        """
        if self.status == "IN_PROGRESS":
            raise ValueError(f"Task '{self.title}' is already in progress")
        
        if self.status == "DONE":
            raise ValueError(f"Cannot start a completed task")
        
        self.status = "IN_PROGRESS"
        self.updated_at = datetime.now()
    
    def complete(self) -> None:
        """Mark the task as complete.
        
        Raises:
            ValueError: If the task is already done
        """
        if self.status == "DONE":
            raise ValueError(f"Task '{self.title}' is already complete")
        
        self.status = "DONE"
        self.completed_at = datetime.now()
        self.updated_at = datetime.now()
    
    def add_dependency(self, task_id: str) -> None:
        """Add a dependency to the task.
        
        Args:
            task_id: ID of the task this task depends on
            
        Raises:
            ValueError: If the dependency already exists
        """
        if task_id in self.depends_on:
            raise ValueError(f"Task '{self.title}' already depends on task with ID {task_id}")
        
        self.depends_on.append(task_id)
        self.updated_at = datetime.now()
    
    def remove_dependency(self, task_id: str) -> None:
        """Remove a dependency from the task.
        
        Args:
            task_id: ID of the task to remove as a dependency
            
        Raises:
            ValueError: If the dependency does not exist
        """
        if task_id not in self.depends_on:
            raise ValueError(f"Task '{self.title}' does not depend on task with ID {task_id}")
        
        self.depends_on.remove(task_id)
        self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the task.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the todo item to a dictionary.
        
        Returns:
            Dictionary representation of the todo item
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "depends_on": self.depends_on,
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoItem':
        """Create a TodoItem from a dictionary.
        
        Args:
            data: Dictionary representation of the todo item
            
        Returns:
            TodoItem instance
        """
        # Handle datetime fields
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            data['created_at'] = datetime.fromisoformat(created_at)
            
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            data['updated_at'] = datetime.fromisoformat(updated_at)
            
        completed_at = data.get('completed_at')
        if completed_at and isinstance(completed_at, str):
            data['completed_at'] = datetime.fromisoformat(completed_at)
        
        # Create the todo item
        return cls(**data)
