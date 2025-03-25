"""
Project Router

This module defines the FastAPI router for project-related endpoints.
It follows the DDD principles by using the domain services through the API service.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from roboco.api.models.project import Project, ProjectCreate, ProjectUpdate
from roboco.api.models.task import Task, TaskCreate, TaskUpdate
from roboco.services.project_service import ProjectService
from roboco.api.dependencies import get_api_service


router = APIRouter(
    tags=["projects"],
    responses={404: {"description": "Project not found"}},
)


@router.get("/", response_model=List[Project])
async def list_projects(api_service = Depends(get_api_service)):
    """
    List all projects.
    
    Returns a list of all configured projects.
    """
    try:
        return await api_service.list_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing projects: {str(e)}")


@router.post("/", response_model=Project, status_code=201)
async def create_project(
    project_create: ProjectCreate,
    api_service = Depends(get_api_service)
):
    """
    Create a new project.
    
    Parameters:
    - name: Name of the project
    - description: Description of the project
    - directory: Optional custom directory name
    - teams: Optional list of team keys
    - tags: Optional tags
    
    Returns the created project.
    """
    try:
        return await api_service.create_project(project_create)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    api_service = Depends(get_api_service)
):
    """
    Get a project by ID.
    
    Parameters:
    - project_id: ID of the project
    
    Returns the project.
    """
    try:
        project = await api_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving project: {str(e)}")


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    api_service = Depends(get_api_service)
):
    """
    Update a project.
    
    Parameters:
    - project_id: ID of the project to update
    - project_update: Fields to update
    
    Returns the updated project.
    """
    try:
        project = await api_service.update_project(project_id, project_update)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    api_service = Depends(get_api_service)
):
    """
    Delete a project.
    
    Parameters:
    - project_id: ID of the project to delete
    
    Returns a success message.
    """
    try:
        success = await api_service.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return {"message": f"Project {project_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {str(e)}")


# Task-related endpoints

@router.post("/{project_id}/tasks", response_model=Task, status_code=201)
async def create_task(
    project_id: str,
    task_create: TaskCreate,
    api_service = Depends(get_api_service)
):
    """
    Create a new task.
    
    Parameters:
    - project_id: ID of the project
    - task_create: Task data
    
    Returns the created task.
    """
    try:
        task = await api_service.create_task(project_id, task_create)
        if not task:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


@router.put("/{project_id}/tasks/{task_id}", response_model=Task)
async def update_task(
    project_id: str,
    task_id: str,
    task_update: TaskUpdate,
    api_service = Depends(get_api_service)
):
    """
    Update a task.
    
    Parameters:
    - project_id: ID of the project
    - task_id: ID of the task to update
    - task_update: Fields to update
    
    Returns the updated task.
    """
    try:
        task = await api_service.update_task(project_id, task_id, task_update)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found in project {project_id}")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task: {str(e)}")


@router.get("/{project_id}/tasks", response_model=List[Task])
async def list_tasks(
    project_id: str,
    api_service = Depends(get_api_service)
):
    """
    List all tasks for a project.
    
    Parameters:
    - project_id: ID of the project
    
    Returns a list of tasks.
    """
    try:
        tasks = await api_service.list_tasks(project_id)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tasks: {str(e)}")


@router.get("/{project_id}/task-md")
async def get_task_markdown(
    project_id: str,
    api_service = Depends(get_api_service)
):
    """
    Get the task.md file for a project.
    
    Parameters:
    - project_id: ID of the project
    
    Returns the markdown content.
    """
    try:
        markdown = await api_service.get_task_markdown(project_id)
        if not markdown:
            raise HTTPException(status_code=404, detail=f"Task markdown not found for project {project_id}")
        return markdown
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task markdown: {str(e)}")
