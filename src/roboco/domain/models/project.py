"""
Project Domain Model

This module defines the Project domain entity and related value objects.
It encapsulates the business logic for project management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from loguru import logger

from roboco.domain.models.sprint import Sprint
from roboco.domain.models.todo_item import TodoItem


class Project:
    """Project domain entity.
    
    This class represents a project in the domain model, encapsulating
    business logic for project management operations.
    
    A project is a high-level organizational unit that contains goals,
    teams, and artifacts such as source code and documents. It can span 
    multiple jobs and provides a way to track progress over time through
    iterations or sprints.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        id: Optional[str] = None,
        directory: Optional[str] = None,
        teams: Optional[List[str]] = None,
        jobs: Optional[List[str]] = None,
        sprints: Optional[List[Sprint]] = None,
        current_sprint: Optional[str] = None,
        todos: Optional[List[TodoItem]] = None,
        tags: Optional[List[str]] = None,
        source_code_dir: str = "src",
        docs_dir: str = "docs",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **extra_fields
    ):
        """Initialize a Project domain entity.
        
        Args:
            name: Name of the project
            description: Description of the project goals
            id: Unique identifier for the project (generated if not provided)
            directory: Directory where project files are stored (derived from name if not provided)
            teams: List of teams involved in this project
            jobs: List of jobs associated with this project
            sprints: List of sprints or iterations planned for this project
            current_sprint: Name of the current active sprint
            todos: Unassigned todo items for the project
            tags: Tags for categorizing the project
            source_code_dir: Directory for source code within the project directory
            docs_dir: Directory for documentation within the project directory
            created_at: When the project was created
            updated_at: When the project was last updated
            **extra_fields: Additional project-specific fields
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.directory = directory or name.lower().replace(" ", "_")
        self.teams = teams or []
        self.jobs = jobs or []
        self.sprints = sprints or []
        self.current_sprint = current_sprint
        self.todos = todos or []
        self.tags = tags or []
        self.source_code_dir = source_code_dir
        self.docs_dir = docs_dir
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        
        # Store any extra fields
        for key, value in extra_fields.items():
            setattr(self, key, value)
    
    def add_team(self, team_name: str) -> None:
        """Add a team to the project.
        
        Args:
            team_name: Name of the team to add
            
        Raises:
            ValueError: If the team already exists in the project
        """
        if team_name in self.teams:
            raise ValueError(f"Team {team_name} already exists in project {self.name}")
        
        self.teams.append(team_name)
        self.updated_at = datetime.now()
    
    def remove_team(self, team_name: str) -> None:
        """Remove a team from the project.
        
        Args:
            team_name: Name of the team to remove
            
        Raises:
            ValueError: If the team does not exist in the project
        """
        if team_name not in self.teams:
            raise ValueError(f"Team {team_name} does not exist in project {self.name}")
        
        self.teams.remove(team_name)
        self.updated_at = datetime.now()
    
    def add_todo(self, todo: TodoItem) -> None:
        """Add a todo item to the project.
        
        Args:
            todo: The todo item to add
        """
        self.todos.append(todo)
        self.updated_at = datetime.now()
    
    def add_sprint(self, sprint: Sprint) -> None:
        """Add a sprint to the project.
        
        Args:
            sprint: The sprint to add
            
        Raises:
            ValueError: If a sprint with the same name already exists
        """
        # Check if a sprint with the same name already exists
        if any(s.name == sprint.name for s in self.sprints):
            raise ValueError(f"Sprint {sprint.name} already exists in project {self.name}")
        
        self.sprints.append(sprint)
        self.updated_at = datetime.now()
    
    def set_current_sprint(self, sprint_name: str) -> None:
        """Set the current active sprint.
        
        Args:
            sprint_name: Name of the sprint to set as current
            
        Raises:
            ValueError: If the sprint does not exist in the project
        """
        # Check if the sprint exists
        if not any(s.name == sprint_name for s in self.sprints):
            raise ValueError(f"Sprint {sprint_name} does not exist in project {self.name}")
        
        self.current_sprint = sprint_name
        self.updated_at = datetime.now()
    
    def get_active_sprint(self) -> Optional[Sprint]:
        """Get the currently active sprint.
        
        Returns:
            The active sprint or None if no sprint is active
        """
        if not self.current_sprint:
            return None
            
        for sprint in self.sprints:
            if sprint.name == self.current_sprint:
                return sprint
                
        return None
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the project.
        
        Args:
            tag: The tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the project to a dictionary.
        
        Returns:
            Dictionary representation of the project
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "directory": self.directory,
            "teams": self.teams,
            "jobs": self.jobs,
            "sprints": [sprint.to_dict() for sprint in self.sprints],
            "current_sprint": self.current_sprint,
            "todos": [todo.to_dict() for todo in self.todos],
            "tags": self.tags,
            "source_code_dir": self.source_code_dir,
            "docs_dir": self.docs_dir,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create a Project from a dictionary.
        
        Args:
            data: Dictionary representation of the project
            
        Returns:
            Project instance
        """
        # Handle datetime fields
        created_at = data.get('created_at')
        if created_at and isinstance(created_at, str):
            data['created_at'] = datetime.fromisoformat(created_at)
            
        updated_at = data.get('updated_at')
        if updated_at and isinstance(updated_at, str):
            data['updated_at'] = datetime.fromisoformat(updated_at)
        
        # Handle nested objects
        sprints_data = data.pop('sprints', [])
        sprints = [Sprint.from_dict(sprint_data) for sprint_data in sprints_data]
        
        todos_data = data.pop('todos', [])
        todos = [TodoItem.from_dict(todo_data) for todo_data in todos_data]
        
        # Create the project
        return cls(
            **data,
            sprints=sprints,
            todos=todos
        )
