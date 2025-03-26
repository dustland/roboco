"""
Roboco API Server

This module implements the FastAPI server for the Roboco API using Domain-Driven Design principles.
It organizes endpoints into routers and uses the domain services through the API service layer.
"""

import os
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from roboco.api.routers import chat, job, project
from roboco.services.chat_service import ChatService
from roboco.services.project_service import ProjectService
from roboco.services.agent_service import AgentService
from roboco.core.models.chat import ChatRequest, ChatResponse
from roboco.core.logger import get_logger
from roboco.core.config import get_workspace, load_config


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
config = load_config()
workspace_dir = get_workspace(config)
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
    It creates the necessary services and injects them into the ApiService.
    
    Returns:
        ApiService: The API service instance.
    """
    # Import here to avoid circular dependency
    from roboco.services.api_service import ApiService
    
    # Create the project service
    project_service = ProjectService()
    
    # Create the agent service
    agent_service = AgentService()
    
    # Create the chat service
    chat_service = ChatService()
    
    # Create the API service with all the required services
    return ApiService(
        project_service=project_service,
        agent_service=agent_service,
        chat_service=chat_service
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
        config = load_config()
        base_dir = os.environ.get("ROBOCO_DATA_DIR", os.path.join(config.workspace_root, ".roboco"))
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


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chat requests."""
    # Lazy import to avoid circular dependency
    from roboco.services.chat_service import ChatService
    
    chat_service = ChatService()
    return await chat_service.start_chat(request)


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    uvicorn.run("roboco.api.server:app", host=host, port=port, reload=True)
