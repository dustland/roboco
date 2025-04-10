"""
Roboco API Server

This module implements the FastAPI server for the Roboco API using Domain-Driven Design principles.
It organizes endpoints into routers and uses the domain services through the API service layer.
"""

import os
from datetime import datetime
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from roboco.api.routers import project, task, chat, files
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
app.include_router(task.router, prefix="/tasks", tags=["tasks"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(files.router, prefix="", tags=["files"])  # No prefix as we use /projects/{project_id}/files in the router


@app.get("/")
async def root():
    """Root endpoint that returns basic API information."""
    return {
        "name": "Roboco API",
        "version": "0.1.0",
        "description": "API for the Roboco project management and agent orchestration system",
        "status": "running with auto-reload"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the API."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"},
    )


# Add middlewares for request/response logging and processing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request details."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.debug(f"Request: {request.method} {request.url.path} ({process_time:.4f}s)")
    return response


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    # Run the server
    uvicorn.run("roboco.api.server:app", host=host, port=port, reload=True)


def run_api_server():
    """
    Entry point for the API server script.
    Run with 'roboco-api' after installing the package.
    """
    import uvicorn
    import multiprocessing
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    # Calculate default workers: Either specified by env var, minimum of 4, or CPU count
    default_workers = int(os.getenv("WORKERS", "4"))
    
    logger.info(f"Starting Roboco API server on {host}:{port} with {default_workers} workers")
    
    # Run the server - use direct app instance for production with multiple workers
    uvicorn.run(
        app, 
        host=host, 
        port=port, 
        workers=default_workers
    )


def run_dev_server():
    """
    Entry point for the API server in development mode with auto-reload.
    Run with 'roboco-api-dev' after installing the package.
    
    Note: In development mode with auto-reload enabled, we can only use a single worker.
    For multi-worker support, use the regular 'roboco-api' command.
    """
    import uvicorn
    
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting Roboco API server in development mode on {host}:{port}")
    logger.info("Auto-reload is enabled - server will restart when code changes")
    logger.warning("Development mode only supports a single worker. For multi-worker support, use 'roboco-api' instead.")
    
    # Run with reload=True for development mode (limited to a single worker)
    uvicorn.run(
        "roboco.api.server:app", 
        host=host, 
        port=port, 
        reload=True,
        reload_dirs=["src/roboco"]
    )
