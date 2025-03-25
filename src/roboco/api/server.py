"""
Roboco API Server

This module implements the FastAPI server for the Roboco API using Domain-Driven Design principles.
It organizes endpoints into routers and uses the domain services through the API service layer.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from roboco.api.routers import chat, job, project
from roboco.services.project_service import ProjectService
from roboco.services.task_service import TaskService
from roboco.services.team_service import TeamService
from roboco.services.agent_service import AgentService
from roboco.services.workspace_service import WorkspaceService
from roboco.services.chat_service import ChatService
from roboco.storage.repositories.file_project_repository import FileProjectRepository


# Create the FastAPI app
app = FastAPI(
    title="Roboco API",
    description="API for the Roboco project management and agent orchestration system",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up workspace directory
workspace_dir = os.path.expanduser("~/roboco_workspace")
os.makedirs(workspace_dir, exist_ok=True)

# Mount static files for the workspace directory
app.mount("/workspace", StaticFiles(directory=workspace_dir), name="workspace")

# Include routers
app.include_router(project.router, prefix="/projects", tags=["projects"])
app.include_router(job.router, prefix="/jobs", tags=["jobs"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


# Dependency for getting the API service
def get_api_service():
    """
    Get the API service instance.
    
    This function follows the Dependency Injection pattern for FastAPI.
    It creates the necessary services and repositories and injects them
    into the ApiService.
    
    Returns:
        ApiService: The API service instance.
    """
    # Import here to avoid circular dependency
    from roboco.services.api_service import ApiService
    
    # Create the project repository
    project_repository = FileProjectRepository()
    
    # Create the project service with the repository
    project_service = ProjectService(project_repository)
    
    # Create the team service
    team_service = TeamService()
    
    # Create the agent service
    agent_service = AgentService()
    
    # Create the task service
    task_service = TaskService(project_repository)
    
    # Create the workspace service
    workspace_service = WorkspaceService()
    
    # Create the chat service
    chat_service = ChatService(project_repository)
    
    # Create the API service with all the required services
    return ApiService(
        project_service=project_service,
        team_service=team_service,
        agent_service=agent_service,
        task_service=task_service,
        workspace_service=workspace_service,
        chat_service=chat_service,
        project_repository=project_repository
    )


@app.get("/")
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "Roboco API",
        "version": "0.1.0",
        "description": "API for the Roboco project management and agent orchestration system",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/artifacts/{path:path}")
async def get_artifact(path: str):
    """
    Get an artifact file.
    
    Parameters:
    - path: Path to the artifact file
    
    Returns the file content.
    """
    try:
        # Construct the absolute path to the artifact
        base_dir = os.environ.get("ROBOCO_DATA_DIR", os.path.expanduser("~/.roboco"))
        artifact_path = os.path.join(base_dir, "artifacts", path)
        
        # Check if the file exists
        if not os.path.exists(artifact_path):
            raise HTTPException(status_code=404, detail=f"Artifact not found: {path}")
        
        # Return the file
        return FileResponse(artifact_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving artifact {path}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving artifact: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the API."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    uvicorn.run("roboco.api.server:app", host=host, port=port, reload=True)
