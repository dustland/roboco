"""
Project Manifest Domain Model

This module defines the ProjectManifest domain entity and related models,
which describe the structure and metadata of a project.
"""

from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from loguru import logger

logger = logger.bind(module=__name__)

# Define Pydantic models for project manifest
class TaskItem(BaseModel):
    """Task definition within a project manifest."""
    title: str = Field(..., description="Title of the task")
    description: str = Field(..., description="Description of the task")
    details: List[str] = Field(default_factory=list, description="Detailed list of task steps or requirements")
    status: str = Field(default="todo", description="Status of the task (todo, in_progress, completed, etc.)")

class ProjectManifest(BaseModel):
    """Manifest describing a project structure and metadata."""
    id: str = Field(..., description="Project unique identifier")
    name: str = Field(..., description="Human-readable project name")
    description: str = Field(..., description="Project description")
    tasks: List[TaskItem] = Field(default_factory=list, description="Tasks for the project")
    
    def tasks_to_markdown(self) -> str:
        """Convert tasks to markdown format.
        
        Returns:
            Markdown string representation of the tasks
        """
        lines = [f"# Tasks for {self.name}", ""]
        
        for task in self.tasks:
            # Add the heading first, then the checkbox as a separate element
            lines.append(f"## Task: {task.title}")
            
            # Add status indicator on the next line, not inside the heading
            status_indicator = "x" if task.status == "completed" else " "
            lines.append(f"- [{status_indicator}] Status: {'Completed' if task.status == 'completed' else 'Todo'}")
            lines.append("")
            
            # Add description
            lines.append(f"{task.description}")
            lines.append("")
            
            # Add details
            if task.details:
                for detail in task.details:
                    lines.append(f"- {detail}")
                lines.append("")
        
        return "\n".join(lines)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "A1c23fb",
                "name": "Todo App",
                "description": "A simple todo application",
                "tasks": [
                    {
                        "title": "Set up project structure",
                        "description": "Create the initial project directory structure",
                        "details": ["Create src directory", "Create docs directory", "Create tests directory"],
                        "status": "todo"
                    },
                    {
                        "title": "Implement core functionality",
                        "description": "Develop the core features of the application",
                        "details": ["Create data models", "Implement business logic", "Set up database connections"],
                        "status": "todo"
                    }
                ]
            }
        }
    }

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

def dict_to_project_manifest(data: Dict[str, Any]) -> ProjectManifest:
    """
    Convert a dictionary to a ProjectManifest.
    
    Args:
        data: Dictionary containing project manifest data
        
    Returns:
        ProjectManifest object
        
    Raises:
        ValueError: If the data is invalid
    """
    return ProjectManifest(**data)
