"""
Project router.

This module defines the FastAPI routes for project-related operations,
including nested task and message resources following the hierarchy.
"""

from typing import List
from fastapi import APIRouter, HTTPException

from roboco.core.models import (
    Project, Task, Message
)
from roboco.api.models import (
    ProjectCreate, ProjectUpdate,
    TaskCreate, TaskUpdate, 
    MessageCreate
)
from roboco.db import service

router = APIRouter(
    tags=["projects"]
)

# Project endpoints
@router.post("/", response_model=Project)
def create_project(project_data: ProjectCreate):
    """Create a new project."""
    return service.create_project(project_data)

@router.get("/", response_model=List[Project])
def get_all_projects():
    """Get all projects."""
    return service.get_all_projects()

@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str):
    """Get a project by ID."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=Project)
def update_project(project_id: str, project_data: ProjectUpdate):
    """Update a project."""
    project = service.update_project(project_id, project_data)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}")
def delete_project(project_id: str):
    """Delete a project."""
    success = service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project deleted successfully"}

# Task endpoints within a project
@router.post("/{project_id}/tasks", response_model=Task)
def create_task(project_id: str, task_data: TaskCreate):
    """Create a new task in a project."""
    task = service.create_task(project_id, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Project not found")
    return task

@router.get("/{project_id}/tasks", response_model=List[Task])
def get_project_tasks(project_id: str):
    """Get all tasks for a project."""
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return service.get_tasks_by_project(project_id)

@router.get("/{project_id}/tasks/{task_id}", response_model=Task)
def get_task(project_id: str, task_id: str):
    """Get a task by ID within a project."""
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    return task

@router.put("/{project_id}/tasks/{task_id}", response_model=Task)
def update_task(project_id: str, task_id: str, task_data: TaskUpdate):
    """Update a task within a project."""
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    
    updated_task = service.update_task(task_id, task_data)
    return updated_task

@router.delete("/{project_id}/tasks/{task_id}")
def delete_task(project_id: str, task_id: str):
    """Delete a task within a project."""
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    
    success = service.delete_task(task_id)
    return {"message": "Task deleted successfully"}

# Message endpoints within a task within a project
@router.post("/{project_id}/tasks/{task_id}/messages", response_model=Message)
def create_message(project_id: str, task_id: str, message_data: MessageCreate):
    """Create a new message in a task within a project."""
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    
    message = service.create_message(task_id, message_data)
    return message

@router.get("/{project_id}/tasks/{task_id}/messages", response_model=List[Message])
def get_task_messages(project_id: str, task_id: str):
    """Get all messages for a task within a project."""
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    
    return service.get_messages_by_task(task_id)

@router.get("/{project_id}/tasks/{task_id}/messages/{message_id}", response_model=Message)
def get_message(project_id: str, task_id: str, message_id: str):
    """Get a specific message in a task within a project."""
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    
    message = service.get_message(message_id)
    if not message or message.task_id != task_id:
        raise HTTPException(status_code=404, detail="Message not found in this task")
    
    return message

@router.delete("/{project_id}/tasks/{task_id}/messages/{message_id}")
def delete_message(project_id: str, task_id: str, message_id: str):
    """Delete a message in a task within a project."""
    task = service.get_task(task_id)
    if not task or task.project_id != project_id:
        raise HTTPException(status_code=404, detail="Task not found in this project")
    
    message = service.get_message(message_id)
    if not message or message.task_id != task_id:
        raise HTTPException(status_code=404, detail="Message not found in this task")
    
    success = service.delete_message(message_id)
    return {"message": "Message deleted successfully"} 