"""
Pydantic Adapters

This module provides adapter functions to convert between domain models and Pydantic DTOs.
These adapters facilitate the transition from a Pydantic-centric architecture to a
domain-driven design while maintaining backward compatibility with the API layer.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from roboco.core.schema import ProjectConfig, Task as PydanticTask
from roboco.core.models.project import Project
from roboco.core.schema import Task as DomainTask  # Import Task from schema.py instead of models/task.py


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
        current_sprint=project_config.current_sprint,
        tasks=[pydantic_to_task(task) for task in project_config.tasks],
        tags=project_config.tags,
        source_code_dir=project_config.source_code_dir,
        docs_dir=project_config.docs_dir,
        created_at=project_config.created_at,
        updated_at=project_config.updated_at
    )


def task_to_pydantic(task: DomainTask) -> PydanticTask:
    """Convert a domain Task to a Pydantic Task.
    
    Args:
        task: Domain Task model
        
    Returns:
        Pydantic Task model
    """
    return PydanticTask(
        id=getattr(task, 'id', None),
        title=getattr(task, 'title', task.description),
        description=task.description,
        status=task.status,
        assigned_to=task.assigned_to,
        priority=task.priority,
        created_at=getattr(task, 'created_at', datetime.now()),
        updated_at=getattr(task, 'updated_at', datetime.now()),
        completed_at=getattr(task, 'completed_at', None),
        due_date=getattr(task, 'due_date', None),
        tags=task.tags,
        metadata=getattr(task, 'metadata', {})
    )


def pydantic_to_task(task_config: PydanticTask) -> DomainTask:
    """Convert a Pydantic Task to a domain Task.
    
    Args:
        task_config: Pydantic Task model
        
    Returns:
        Domain Task model
    """
    return DomainTask(
        description=task_config.description,
        status=task_config.status,
        assigned_to=task_config.assigned_to,
        priority=task_config.priority,
        tags=task_config.tags
    )
