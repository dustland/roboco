"""
Project Domain Model

This module defines the Project domain entity and related value objects.
It encapsulates the business logic for project management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from loguru import logger

from roboco.core.models.task import Task


class Project:
    """Project domain entity.
    
    This class represents a project in the domain model, encapsulating
    business logic for project management operations.
    
    A project is a high-level organizational unit that contains goals,
    teams, and artifacts such as source code and documents. It provides 
    a way to track progress through tasks.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        directory: str,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        teams: Optional[List[str]] = None,
        jobs: Optional[List[str]] = None,
        tasks: Optional[List[Task]] = None,
        tags: Optional[List[str]] = None,
        source_code_dir: str = "src",
        docs_dir: str = "docs",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a project.
        
        Args:
            name: Name of the project
            description: Description of the project goals
            directory: Directory where project files are stored
            id: Unique identifier for the project
            created_at: When the project was created
            updated_at: When the project was last updated
            teams: Teams involved in this project
            jobs: Jobs associated with this project
            tasks: Tasks for the project
            tags: Tags for categorizing the project
            source_code_dir: Directory for source code within the project directory
            docs_dir: Directory for documentation within the project directory
            metadata: Additional metadata for the project
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.directory = directory
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.teams = teams or []
        self.jobs = jobs or []
        self.tasks = tasks or []
        self.tags = tags or []
        self.source_code_dir = source_code_dir
        self.docs_dir = docs_dir
        self.metadata = metadata or {}
    
    def add_task(self, task: Task) -> None:
        """Add a task to the project.
        
        Args:
            task: The task to add
        """
        self.tasks.append(task)
        self.updated_at = datetime.now()
    
    def add_job(self, job_id: str) -> None:
        """Add a job to the project.
        
        Args:
            job_id: ID of the job to add
        """
        if job_id not in self.jobs:
            self.jobs.append(job_id)
            self.updated_at = datetime.now()
    
    def add_team(self, team_id: str) -> None:
        """Add a team to the project.
        
        Args:
            team_id: ID of the team to add
        """
        if team_id not in self.teams:
            self.teams.append(team_id)
            self.updated_at = datetime.now()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the project.
        
        Args:
            tag: Tag to add
        """
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the project.
        
        Args:
            tag: Tag to remove
        """
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def update_metadata(self, key: str, value: Any) -> None:
        """Update a metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
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
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "teams": self.teams,
            "jobs": self.jobs,
            "tasks": [task.dict() for task in self.tasks],
            "tags": self.tags,
            "source_code_dir": self.source_code_dir,
            "docs_dir": self.docs_dir,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create a project from a dictionary.
        
        Args:
            data: Dictionary representation of the project
            
        Returns:
            Project instance
        """
        # Convert string dates to datetime
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
            
        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # Convert task dictionaries to Task objects
        tasks = []
        for task_data in data.get("tasks", []):
            if isinstance(task_data, dict):
                tasks.append(Task(**task_data))
            else:
                tasks.append(task_data)
        
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            description=data.get("description"),
            directory=data.get("directory"),
            created_at=created_at,
            updated_at=updated_at,
            teams=data.get("teams", []),
            jobs=data.get("jobs", []),
            tasks=tasks,
            tags=data.get("tags", []),
            source_code_dir=data.get("source_code_dir", "src"),
            docs_dir=data.get("docs_dir", "docs"),
            metadata=data.get("metadata", {})
        )
