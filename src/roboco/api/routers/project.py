"""
Project Router

This module defines the FastAPI router for project-related endpoints.
It follows the DDD principles by using the domain services through the API service.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from roboco.services.api_service import ApiService
from roboco.api.schemas.project import Project, ProjectCreate, ProjectUpdate
from roboco.api.schemas.sprint import Sprint, SprintCreate, SprintUpdate
from roboco.api.schemas.todo import TodoItem, TodoItemCreate, TodoItemUpdate
from roboco.infrastructure.repositories.file_project_repository import FileProjectRepository
from roboco.services.project_service import ProjectService


router = APIRouter(
    tags=["projects"],
    responses={404: {"description": "Project not found"}},
)


# Dependency to get the API service
async def get_api_service():
    """Get the API service instance."""
    # Create the repository
    repository = FileProjectRepository()
    
    # Create the domain service
    project_service = ProjectService(repository)
    
    # Create the API service - pass the repository directly
    api_service = ApiService(project_service, project_repository=repository)
    
    return api_service


@router.get("/", response_model=List[Project])
async def list_projects(api_service: ApiService = Depends(get_api_service)):
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
    api_service: ApiService = Depends(get_api_service)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {str(e)}")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Get a project by ID.
    
    Parameters:
    - project_id: ID of the project
    
    Returns the project.
    """
    project = await api_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Update a project.
    
    Parameters:
    - project_id: ID of the project to update
    - project_update: Fields to update
    
    Returns the updated project.
    """
    try:
        return await api_service.update_project(project_id, project_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating project: {str(e)}")


@router.delete("/{project_id}", response_model=dict)
async def delete_project(
    project_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Delete a project.
    
    Parameters:
    - project_id: ID of the project to delete
    
    Returns a success message.
    """
    success = await api_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    return {"message": f"Project with ID {project_id} deleted successfully"}


# Sprint-related endpoints

@router.post("/{project_id}/sprints", response_model=Sprint, status_code=201)
async def create_sprint(
    project_id: str,
    sprint_create: SprintCreate,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Create a new sprint.
    
    Parameters:
    - project_id: ID of the project
    - sprint_create: Sprint data
    
    Returns the created sprint.
    """
    try:
        return await api_service.create_sprint(project_id, sprint_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating sprint: {str(e)}")


@router.put("/{project_id}/sprints/{sprint_name}", response_model=Sprint)
async def update_sprint(
    project_id: str,
    sprint_name: str,
    sprint_update: SprintUpdate,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Update a sprint.
    
    Parameters:
    - project_id: ID of the project
    - sprint_name: Name of the sprint to update
    - sprint_update: Fields to update
    
    Returns the updated sprint.
    """
    try:
        return await api_service.update_sprint(project_id, sprint_name, sprint_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating sprint: {str(e)}")


# Todo-related endpoints

@router.post("/{project_id}/todos", response_model=TodoItem, status_code=201)
async def create_todo(
    project_id: str,
    todo_create: TodoItemCreate,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Create a new todo item.
    
    Parameters:
    - project_id: ID of the project
    - todo_create: Todo item data
    
    Returns the created todo item.
    """
    try:
        return await api_service.create_todo(project_id, todo_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating todo: {str(e)}")


@router.put("/{project_id}/todos/{todo_id}", response_model=TodoItem)
async def update_todo(
    project_id: str,
    todo_id: str,
    todo_update: TodoItemUpdate,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Update a todo item.
    
    Parameters:
    - project_id: ID of the project
    - todo_id: ID of the todo to update
    - todo_update: Fields to update
    
    Returns the updated todo item.
    """
    try:
        return await api_service.update_todo(project_id, todo_id, todo_update)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating todo: {str(e)}")
