"""
Pydantic Adapters

This module provides adapter functions to convert between domain models and Pydantic DTOs.
These adapters facilitate the transition from a Pydantic-centric architecture to a
domain-driven design while maintaining backward compatibility with the API layer.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from roboco.core.schema import ProjectConfig, TodoItem as PydanticTodoItem, Sprint as PydanticSprint, Task
from roboco.core.models.project import Project
from roboco.core.models.sprint import Sprint
from roboco.core.models.todo_item import TodoItem


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
        todos=[todo_to_pydantic(todo) for todo in project.todos],
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
        sprints=[pydantic_to_sprint(sprint) for sprint in project_config.sprints],
        current_sprint=project_config.current_sprint,
        todos=[pydantic_to_todo(todo) for todo in project_config.todos],
        tags=project_config.tags,
        source_code_dir=project_config.source_code_dir,
        docs_dir=project_config.docs_dir,
        created_at=project_config.created_at,
        updated_at=project_config.updated_at
    )


def sprint_to_pydantic(sprint: Sprint) -> PydanticSprint:
    """Convert a domain Sprint to a Pydantic Sprint.
    
    Args:
        sprint: Domain Sprint model
        
    Returns:
        Pydantic Sprint model
    """
    return PydanticSprint(
        id=sprint.id,
        name=sprint.name,
        description=sprint.description,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        status=sprint.status,
        todos=[todo_to_pydantic(todo) for todo in sprint.todos],
        tags=sprint.tags
    )


def pydantic_to_sprint(sprint_config: PydanticSprint) -> Sprint:
    """Convert a Pydantic Sprint to a domain Sprint.
    
    Args:
        sprint_config: Pydantic Sprint model
        
    Returns:
        Domain Sprint model
    """
    return Sprint(
        id=sprint_config.id,
        name=sprint_config.name,
        description=sprint_config.description,
        start_date=sprint_config.start_date,
        end_date=sprint_config.end_date,
        status=sprint_config.status,
        todos=[pydantic_to_todo(todo) for todo in sprint_config.todos],
        tags=sprint_config.tags
    )


def todo_to_pydantic(todo: TodoItem) -> PydanticTodoItem:
    """Convert a domain TodoItem to a Pydantic TodoItem.
    
    Args:
        todo: Domain TodoItem model
        
    Returns:
        Pydantic TodoItem model
    """
    return PydanticTodoItem(
        id=todo.id,
        title=todo.title,
        description=todo.description,
        status=todo.status,
        assigned_to=todo.assigned_to,
        priority=todo.priority,
        created_at=todo.created_at,
        updated_at=todo.updated_at,
        completed_at=todo.completed_at,
        depends_on=todo.depends_on,
        tags=todo.tags
    )


def pydantic_to_todo(todo_config: PydanticTodoItem) -> TodoItem:
    """Convert a Pydantic TodoItem to a domain TodoItem.
    
    Args:
        todo_config: Pydantic TodoItem model
        
    Returns:
        Domain TodoItem model
    """
    return TodoItem(
        id=todo_config.id,
        title=todo_config.title,
        description=todo_config.description,
        status=todo_config.status,
        assigned_to=todo_config.assigned_to,
        priority=todo_config.priority,
        created_at=todo_config.created_at,
        updated_at=todo_config.updated_at,
        completed_at=todo_config.completed_at,
        depends_on=todo_config.depends_on,
        tags=todo_config.tags
    )
