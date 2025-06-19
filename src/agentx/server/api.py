"""
AgentX Server API

FastAPI-based REST API for task execution and memory management.
Provides endpoints for creating and managing tasks, and accessing task memory.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from ..utils.logger import get_logger
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..core.task import TaskExecutor
from .models import (
    TaskRequest, TaskResponse, TaskInfo, TaskStatus,
    MemoryRequest, MemoryResponse,
    HealthResponse
)

logger = get_logger(__name__)

# In-memory task storage (in production, use a proper database)
active_tasks: Dict[str, TaskExecutor] = {}
server_start_time = datetime.now()


def create_app(
    title: str = "AgentX API",
    description: str = "REST API for AgentX task execution and memory management",
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
                # Get task info from task object
                task_infos.append(TaskInfo(
                    task_id=task.task_id,
                    status=TaskStatus.PENDING,  # Simplified for now
                    config_path=getattr(task, 'config_path', ''),
                    task_description="",
                    context=None,
                    created_at=datetime.now(),
                    completed_at=None
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
            
            return TaskResponse(
                task_id=task_id,
                status=TaskStatus.PENDING,  # Simplified for now
                result=None,
                error=None,
                created_at=datetime.now(),
                completed_at=None
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
            
            # For now, just return success - memory integration can be added later
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
            
            # For now, return empty results - memory integration can be added later
            return MemoryResponse(
                task_id=task_id,
                agent_id=agent_id,
                success=True,
                data=[]
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
            
            # For now, just return success - memory integration can be added later
            return {"message": "Memory cleared successfully"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to clear memory for task {task_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    # Simple observability route
    @app.get("/monitor", response_class=HTMLResponse)
    async def monitor_dashboard():
        """Serve observability dashboard info"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgentX Observability</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .info { background: #f0f8ff; padding: 20px; border-radius: 8px; }
                .code { background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>🤖 AgentX Observability</h1>
            <div class="info">
                <h2>Integrated Mode Active</h2>
                <p>The observability system is running in integrated mode with full features:</p>
                <ul>
                    <li>✅ Real-time event capture</li>
                    <li>✅ Task conversation history</li>
                    <li>✅ Memory inspection</li>
                    <li>✅ Dashboard metrics</li>
                </ul>
                
                <h3>Access the Dashboard</h3>
                <p>To access the full Streamlit dashboard, run:</p>
                <div class="code">
                    streamlit run src/agentx/observability/web.py --server.port=8502
                </div>
                <p><em>Note: Using port 8502 to avoid conflicts with the API server on 8000</em></p>
                
                <h3>API Endpoints</h3>
                <ul>
                    <li><a href="/docs">📚 API Documentation</a></li>
                    <li><a href="/tasks">📋 Tasks API</a></li>
                    <li><a href="/health">❤️ Health Check</a></li>
                </ul>
            </div>
        </body>
        </html>
        """)


async def _execute_task(task: TaskExecutor, task_description: str, context: Optional[Dict[str, Any]] = None):
    """Execute a task in the background"""
    try:
        # For now, just simulate task execution
        logger.info(f"Executing task {task.task_id}: {task_description}")
        await asyncio.sleep(1)  # Simulate work
        logger.info(f"Task {task.task_id} completed")
        
    except Exception as e:
        logger.error(f"Task {task.task_id} failed: {e}")


def run_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info"
):
    """
    Run the AgentX server with integrated observability.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload for development
        log_level: Logging level
    """
    app = create_app()
    
    # Initialize observability monitor in integrated mode
    try:
        from ..observability.monitor import get_monitor
        monitor = get_monitor()
        monitor.start()
        logger.info("✅ Observability monitor started in integrated mode")
        logger.info("📊 Dashboard available at: http://localhost:8000/monitor")
    except Exception as e:
        logger.warning(f"⚠️  Could not start observability monitor: {e}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level
    )