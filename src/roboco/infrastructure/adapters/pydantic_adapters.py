"""
Pydantic Adapters

This module provides adapter functions to convert between domain models and Pydantic DTOs.
These adapters facilitate the transition from a Pydantic-centric architecture to a
domain-driven design while maintaining backward compatibility with the API layer.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from roboco.core.schema import ProjectConfig, Sprint as PydanticSprint, Task as PydanticTask
from roboco.core.models.project import Project
from roboco.core.models.task import Task


def project_to_pydantic(project: Project) -> ProjectConfig:
    """Convert a domain Project to a Pydantic ProjectConfig.
    
    Args:
        project: Domain Project model
        
    Returns:
        Pydantic ProjectConfig model
    """
    return ProjectConfig(
        id=project.id,
        name=project.name,
        description=project.description,
        directory=project.directory,
        teams=project.teams,
        jobs=project.jobs,
        sprints=[sprint_to_pydantic(sprint) for sprint in project.sprints],
        current_sprint=project.current_sprint,
        tasks=[task_to_pydantic(task) for task in project.tasks],
        tags=project.tags,
        source_code_dir=project.source_code_dir,
        docs_dir=project.docs_dir,
        created_at=project.created_at,
        updated_at=project.updated_at
    )


def pydantic_to_project(project_config: ProjectConfig) -> Project:
    """Convert a Pydantic ProjectConfig to a domain Project.
    
    Args:
        project_config: Pydantic ProjectConfig model
        
    Returns:
        Domain Project model
    """
    return Project(
        id=project_config.id,
        name=project_config.name,
        description=project_config.description,
        directory=project_config.directory,
        teams=project_config.teams,
        jobs=project_config.jobs,
        sprints=[],  # Simplified as Sprint model is being removed
        current_sprint=project_config.current_sprint,
        tasks=[pydantic_to_task(task) for task in project_config.tasks],
        tags=project_config.tags,
        source_code_dir=project_config.source_code_dir,
        docs_dir=project_config.docs_dir,
        created_at=project_config.created_at,
        updated_at=project_config.updated_at
    )


def sprint_to_pydantic(sprint: Any) -> PydanticSprint:
    """Convert a domain Sprint to a Pydantic Sprint.
    
    Args:
        sprint: Domain Sprint model
        
    Returns:
        Pydantic Sprint model
    """
    # Simplified as Sprint model is being removed
    return PydanticSprint(
        id=sprint.id,
        name=sprint.name,
        description=sprint.description,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        status=sprint.status,
        tasks=[task_to_pydantic(task) for task in getattr(sprint, 'tasks', [])],
        tags=sprint.tags
    )


def pydantic_to_sprint(sprint_config: PydanticSprint) -> Any:
    """Convert a Pydantic Sprint to a domain Sprint.
    
    Args:
        sprint_config: Pydantic Sprint model
        
    Returns:
        Domain Sprint model
    """
    # Simplified as Sprint model is being removed
    return {
        "id": sprint_config.id,
        "name": sprint_config.name,
        "description": sprint_config.description,
        "start_date": sprint_config.start_date,
        "end_date": sprint_config.end_date,
        "status": sprint_config.status,
        "tasks": [pydantic_to_task(task) for task in sprint_config.tasks],
        "tags": sprint_config.tags
    }


def task_to_pydantic(task: Task) -> PydanticTask:
    """Convert a domain Task to a Pydantic Task.
    
    Args:
        task: Domain Task model
        
    Returns:
        Pydantic Task model
    """
    return PydanticTask(
        id=task.id,
        title=task.title,
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        priority=task.priority,
        created_at=task.created_at,
        updated_at=task.updated_at,
        completed_at=task.completed_at,
        due_date=task.due_date,
        tags=task.tags,
        metadata=task.metadata
    )


def pydantic_to_task(task_config: PydanticTask) -> Task:
    """Convert a Pydantic Task to a domain Task.
    
    Args:
        task_config: Pydantic Task model
        
    Returns:
        Domain Task model
    """
    return Task(
        id=task_config.id,
        title=task_config.title,
        description=task_config.description,
        status=task_config.status,
        assigned_to=task_config.assigned_to,
        priority=task_config.priority,
        created_at=task_config.created_at,
        updated_at=task_config.updated_at,
        completed_at=task_config.completed_at,
        due_date=task_config.due_date,
        tags=task_config.tags,
        metadata=task_config.metadata
    )
