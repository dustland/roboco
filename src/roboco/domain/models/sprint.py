"""
Sprint Domain Model

This module defines the Sprint domain entity and related value objects.
It encapsulates the business logic for sprint management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from loguru import logger

# Forward reference to avoid circular imports
TodoItem = Any  # This will be properly imported by users of this module


class Sprint:
    """Sprint domain entity.
    
    This class represents a sprint or iteration in a project, encapsulating
    business logic for sprint management operations.
    
    A sprint is a time-boxed period during which specific work has to be completed
    and made ready for review.
    """
    
    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: str = "planned",
        todos: Optional[List[TodoItem]] = None,
        tags: Optional[List[str]] = None,
        id: Optional[str] = None,
        **extra_fields
    ):
        """Initialize a Sprint domain entity.
        
        Args:
            name: Name of the sprint
            description: Description of the sprint goals
            start_date: Start date of the sprint
            end_date: End date of the sprint
            status: Status of the sprint (planned, active, completed)
            todos: Todo items scheduled for this sprint
            tags: Tags for categorizing the sprint
            id: Unique identifier for the sprint (generated if not provided)
            **extra_fields: Additional sprint-specific fields
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.start_date = start_date or datetime.now()
        self.end_date = end_date or (datetime.now() if start_date is None else None)
        self.status = status
        self.todos = todos or []
        self.tags = tags or []
        
        # Store any extra fields
        for key, value in extra_fields.items():
            setattr(self, key, value)
    
    def add_todo(self, todo: TodoItem) -> None:
        """Add a todo item to the sprint.
        
        Args:
            todo: The todo item to add
        """
        self.todos.append(todo)
    
    def remove_todo(self, todo_id: str) -> None:
        """Remove a todo item from the sprint.
        
        Args:
            todo_id: ID of the todo item to remove
            
        Raises:
            ValueError: If the todo item does not exist in the sprint
        """
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                self.todos.pop(i)
                return
                
        raise ValueError(f"Todo item with ID {todo_id} not found in sprint {self.name}")
    
    def start(self) -> None:
        """Start the sprint.
        
        Raises:
            ValueError: If the sprint is already active or completed
        """
        if self.status == "active":
            raise ValueError(f"Sprint {self.name} is already active")
        
        if self.status == "completed":
            raise ValueError(f"Cannot start a completed sprint")
        
        self.status = "active"
        if not self.start_date:
            self.start_date = datetime.now()
    
    def complete(self) -> None:
        """Complete the sprint.
        
        Raises:
            ValueError: If the sprint is not active
        """
        if self.status != "active":
            raise ValueError(f"Cannot complete sprint {self.name} that is not active")
        
        self.status = "completed"
        if not self.end_date:
            self.end_date = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the sprint.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
    
    def get_team_sequence(self) -> List[str]:
        """Get the team sequence for this sprint.
        
        Returns:
            List of team names in sequence
        """
        for tag in self.tags:
            if tag.startswith("team_sequence:"):
                return tag.split(":", 1)[1].split(",")
        return []
    
    def set_team_sequence(self, teams: List[str]) -> None:
        """Set the team sequence for this sprint.
        
        Args:
            teams: List of team names in sequence
        """
        # Remove any existing team sequence tag
        self.tags = [tag for tag in self.tags if not tag.startswith("team_sequence:")]
        
        # Add the new team sequence tag
        if teams:
            team_sequence_tag = f"team_sequence:{','.join(teams)}"
            self.tags.append(team_sequence_tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the sprint to a dictionary.
        
        Returns:
            Dictionary representation of the sprint
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "todos": [todo.to_dict() for todo in self.todos],
            "tags": self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Sprint':
        """Create a Sprint from a dictionary.
        
        Args:
            data: Dictionary representation of the sprint
            
        Returns:
            Sprint instance
        """
        # Handle datetime fields
        start_date = data.get('start_date')
        if start_date and isinstance(start_date, str):
            data['start_date'] = datetime.fromisoformat(start_date)
            
        end_date = data.get('end_date')
        if end_date and isinstance(end_date, str):
            data['end_date'] = datetime.fromisoformat(end_date)
        
        # Handle nested objects - we'll handle todos later to avoid circular imports
        todos_data = data.pop('todos', [])
        
        # Create the sprint without todos
        sprint = cls(**data, todos=[])
        
        # Now we can safely import TodoItem and add the todos
        from roboco.domain.models.todo_item import TodoItem
        for todo_data in todos_data:
            sprint.todos.append(TodoItem.from_dict(todo_data))
        
        return sprint
