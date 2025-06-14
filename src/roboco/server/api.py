"""
RoboCo Server API

FastAPI-based REST API for task execution and memory management.
Provides endpoints for creating and managing tasks, and accessing task memory.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..core.task import create_task, Task
from ..core.memory import TaskMemory, AgentMemory
from .models import (
    TaskRequest, TaskResponse, TaskInfo, TaskStatus,
    MemoryRequest, MemoryResponse,
    HealthResponse
)

logger = logging.getLogger(__name__)

# In-memory task storage (in production, use a proper database)
active_tasks: Dict[str, Task] = {}
server_start_time = datetime.now()


def create_app(
    title: str = "RoboCo API",
    description: str = "REST API for RoboCo task execution and memory management",
    version: str = "0.4.0",
    enable_cors: bool = True
) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        title: API title
        description: API description  
        version: API version
        enable_cors: Whether to enable CORS middleware
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version
    )
    
    # Add CORS middleware if enabled
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add routes
    add_routes(app)
    
    return app


def add_routes(app: FastAPI):
    """Add API routes to the FastAPI application"""
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint"""
        return HealthResponse(
            active_tasks=len(active_tasks)
        )
    
    @app.post("/tasks", response_model=TaskResponse)
    async def create_task_endpoint(
        request: TaskRequest,
        background_tasks: BackgroundTasks
    ):
        """Create and start a new task"""
        try:
            # Create the task
            task = create_task(request.config_path)
            active_tasks[task.task_id] = task
            
            # Start task execution in background
            background_tasks.add_task(
                _execute_task,
                task,
                request.task_description,
                request.context
            )
            
            return TaskResponse(
                task_id=task.task_id,
                status=TaskStatus.PENDING
            )
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/tasks", response_model=List[TaskInfo])
    async def list_tasks():
        """List all tasks"""
        try:
            task_infos = []
            for task in active_tasks.values():
                state = task.get_memory().get_state()
                task_infos.append(TaskInfo(
                    task_id=task.task_id,
                    status=TaskStatus(state.get("status", "pending")),
                    config_path=task.config_path,
                    task_description=state.get("task_description", ""),
                    context=state.get("context"),
                    created_at=datetime.fromisoformat(state.get("created_at", datetime.now().isoformat())),
                    completed_at=datetime.fromisoformat(state["completed_at"]) if state.get("completed_at") else None
                ))
            return task_infos
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/tasks/{task_id}", response_model=TaskResponse)
    async def get_task(task_id: str):
        """Get task status and result"""
        try:
            task = active_tasks.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            state = task.get_memory().get_state()
            
            return TaskResponse(
                task_id=task_id,
                status=TaskStatus(state.get("status", "pending")),
                result=state.get("result"),
                error=state.get("error"),
                created_at=datetime.fromisoformat(state.get("created_at", datetime.now().isoformat())),
                completed_at=datetime.fromisoformat(state["completed_at"]) if state.get("completed_at") else None
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/tasks/{task_id}")
    async def delete_task(task_id: str):
        """Delete a task and its memory"""
        try:
            task = active_tasks.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            # Delete task memory and state
            await task.delete()
            
            # Remove from active tasks
            del active_tasks[task_id]
            
            return {"message": "Task deleted successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/tasks/{task_id}/memory", response_model=MemoryResponse)
    async def add_memory(task_id: str, request: MemoryRequest):
        """Add content to task memory"""
        try:
            task = active_tasks.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if not request.content:
                raise HTTPException(status_code=400, detail="Content is required")
            
            if request.agent_id:
                # Add to agent-specific memory
                agent_memory = AgentMemory(agent_id=request.agent_id, task_id=task_id)
                agent_memory.add(request.content)
            else:
                # Add to task memory
                task.get_memory().add(request.content)
            
            return MemoryResponse(
                task_id=task_id,
                agent_id=request.agent_id,
                success=True
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to add memory to task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/tasks/{task_id}/memory", response_model=MemoryResponse)
    async def search_memory(task_id: str, query: Optional[str] = None, agent_id: Optional[str] = None):
        """Search task memory"""
        try:
            task = active_tasks.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if agent_id:
                # Search agent-specific memory
                agent_memory = AgentMemory(agent_id=agent_id, task_id=task_id)
                if query:
                    results = agent_memory.search(query)
                else:
                    results = agent_memory.get_all()
            else:
                # Search task memory
                if query:
                    results = task.get_memory().search(query)
                else:
                    results = task.get_memory().get_all()
            
            return MemoryResponse(
                task_id=task_id,
                agent_id=agent_id,
                success=True,
                data=results
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to search memory for task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/tasks/{task_id}/memory")
    async def clear_memory(task_id: str, agent_id: Optional[str] = None):
        """Clear task memory"""
        try:
            task = active_tasks.get(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            
            if agent_id:
                # Clear agent-specific memory
                agent_memory = AgentMemory(agent_id=agent_id, task_id=task_id)
                agent_memory.clear()
            else:
                # Clear task memory
                task.get_memory().clear()
            
            return {"message": "Memory cleared successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to clear memory for task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def _execute_task(task: Task, task_description: str, context: Optional[Dict[str, Any]] = None):
    """Execute a task in the background"""
    try:
        # Update task state
        memory = task.get_memory()
        memory.set_state({
            "status": "running",
            "task_description": task_description,
            "context": context,
            "created_at": datetime.now().isoformat()
        })
        
        # Execute the task
        result = await task.run(task_description, context or {})
        
        # Update completion state
        memory.set_state({
            "status": "completed",
            "task_description": task_description,
            "context": context,
            "result": result.model_dump() if hasattr(result, 'model_dump') else result,
            "created_at": memory.get_state().get("created_at"),
            "completed_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Task {task.task_id} failed: {e}")
        # Update error state
        memory = task.get_memory()
        memory.set_state({
            "status": "failed",
            "task_description": task_description,
            "context": context,
            "error": str(e),
            "created_at": memory.get_state().get("created_at"),
            "completed_at": datetime.now().isoformat()
        })


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info"
):
    """
    Run the RoboCo server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
        log_level: Logging level
    """
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    ) 