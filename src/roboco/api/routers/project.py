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
    ProjectCreate, ProjectUpdate
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

@router.post("/{project_id}/stop")
def stop_project_execution(project_id: str):
    """Stop the execution of a project.
    
    This endpoint attempts to gracefully stop any ongoing execution
    for the specified project. It will return success even if no
    execution is currently running.
    """
    from roboco.core.project_manager import ProjectManager
    
    # Check if project exists
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Load project manager
        project_manager = ProjectManager.load(project_id)
        
        # Set project status to stopped
        project.meta = project.meta or {}
        project.meta["execution_status"] = "stopped"
        project.meta["stopped_at"] = str(Project.now())
        service.update_project(project_id, project)
        
        return {"success": True, "message": f"Execution stopped for project {project_id}"}
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop project execution: {str(e)}"
        )

# Task endpoints within a project (read-only)
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

# Message endpoints within a task within a project (read-only)
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