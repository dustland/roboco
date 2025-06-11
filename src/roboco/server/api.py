"""
RoboCo Server API

FastAPI-based REST API for multi-user session management and collaboration.
Provides endpoints for session management, collaboration execution, and context operations.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator
from contextlib import asynccontextmanager
import logging
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .session_manager import SessionManager
from .models import (
    SessionConfig, SessionInfo, SessionStatus,
    CollaborationRequest, CollaborationResponse,
    ContextRequest, ContextResponse,
    HealthResponse
)

logger = logging.getLogger(__name__)

# Global session manager
session_manager: Optional[SessionManager] = None
server_start_time = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global session_manager
    
    # Startup
    session_manager = SessionManager()
    await session_manager.start()
    logger.info("RoboCo server started")
    
    yield
    
    # Shutdown
    if session_manager:
        await session_manager.stop()
    logger.info("RoboCo server stopped")


def create_app(
    title: str = "RoboCo Server",
    description: str = "Multi-user collaboration server for RoboCo framework",
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
        version=version,
        lifespan=lifespan
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


def get_session_manager() -> SessionManager:
    """Dependency to get the session manager"""
    if session_manager is None:
        raise HTTPException(status_code=500, detail="Session manager not initialized")
    return session_manager


def add_routes(app: FastAPI):
    """Add API routes to the FastAPI application"""
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check(sm: SessionManager = Depends(get_session_manager)):
        """Health check endpoint"""
        stats = await sm.get_stats()
        uptime = datetime.now() - server_start_time
        
        return HealthResponse(
            active_sessions=stats["active_sessions"],
            total_sessions=stats["total_sessions"],
            uptime=uptime
        )
    
    @app.post("/sessions", response_model=SessionInfo)
    async def create_session(
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        config: Optional[SessionConfig] = None,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Create a new session"""
        try:
            session_info = await sm.create_session(user_id, metadata, config)
            return session_info
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/sessions", response_model=List[SessionInfo])
    async def list_sessions(
        user_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """List sessions with optional filtering"""
        try:
            sessions = await sm.list_sessions(user_id, status)
            return sessions
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/sessions/{session_id}", response_model=SessionInfo)
    async def get_session(
        session_id: str,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Get session information"""
        try:
            session = await sm.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            return session.info
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/sessions/{session_id}")
    async def delete_session(
        session_id: str,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Delete a session"""
        try:
            deleted = await sm.delete_session(session_id)
            if not deleted:
                raise HTTPException(status_code=404, detail="Session not found")
            return {"message": "Session deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/collaborations", response_model=CollaborationResponse)
    async def start_collaboration(
        request: CollaborationRequest,
        background_tasks: BackgroundTasks,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Start a new collaboration"""
        try:
            async with sm.session_context(request.session_id) as session:
                collaboration_id = await session.run(
                    team_config_path=request.team_config_path,
                    task=request.task,
                    context=request.context
                )
                
                # Start collaboration in background
                background_tasks.add_task(
                    _execute_collaboration,
                    session,
                    collaboration_id,
                    request.team_config_path,
                    request.task
                )
                
                response = CollaborationResponse(
                    collaboration_id=collaboration_id,
                    session_id=request.session_id,
                    status="started"
                )
                
                return response
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to start collaboration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/collaborations/{collaboration_id}", response_model=CollaborationResponse)
    async def get_collaboration(
        collaboration_id: str,
        session_id: str,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Get collaboration status"""
        try:
            async with sm.session_context(session_id) as session:
                collab = await session.get_collaboration(collaboration_id)
                if not collab:
                    raise HTTPException(status_code=404, detail="Collaboration not found")
                
                response = CollaborationResponse(
                    collaboration_id=collaboration_id,
                    session_id=session_id,
                    status=collab["status"],
                    result=collab.get("result"),
                    error=collab.get("error"),
                    created_at=collab["created_at"],
                    completed_at=collab.get("completed_at")
                )
                
                return response
                
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get collaboration {collaboration_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/collaborations/stream")
    async def stream_collaboration(
        request: CollaborationRequest,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Start a streaming collaboration"""
        try:
            async with sm.session_context(request.session_id) as session:
                collaboration_id = await session.run(
                    team_config_path=request.team_config_path,
                    task=request.task,
                    context=request.context
                )
                
                async def generate_stream():
                    try:
                        async for event in _stream_collaboration(
                            session,
                            collaboration_id,
                            request.team_config_path,
                            request.task
                        ):
                            yield f"data: {event}\n\n"
                    except Exception as e:
                        error_event = json.dumps({
                            "error": str(e), 
                            "collaboration_id": collaboration_id
                        })
                        yield f"data: {error_event}\n\n"
                
                return StreamingResponse(
                    generate_stream(),
                    media_type="text/plain",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                        "Content-Type": "text/event-stream"
                    }
                )
                
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to start streaming collaboration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/context", response_model=ContextResponse)
    async def context_operation(
        request: ContextRequest,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Perform context operations (save, load, list, delete)"""
        try:
            async with sm.session_context(request.session_id) as session:
                context_store = session.context_store
                
                if request.operation == "save":
                    if not request.key or request.data is None:
                        raise HTTPException(status_code=400, detail="Key and data required for save operation")
                    
                    await context_store.set_scratchpad(request.session_id, request.key, request.data)
                    session.info.context_entries += 1
                    
                    return ContextResponse(
                        session_id=request.session_id,
                        operation=request.operation,
                        success=True
                    )
                
                elif request.operation == "load":
                    if not request.key:
                        raise HTTPException(status_code=400, detail="Key required for load operation")
                    
                    data = await context_store.get_scratchpad(request.session_id, request.key)
                    
                    return ContextResponse(
                        session_id=request.session_id,
                        operation=request.operation,
                        success=True,
                        data=data
                    )
                
                elif request.operation == "list":
                    # For list, we'll need to implement a method to get all keys for a session
                    # For now, return empty list
                    return ContextResponse(
                        session_id=request.session_id,
                        operation=request.operation,
                        success=True,
                        data={"keys": []}  # Would need custom implementation
                    )
                
                elif request.operation == "delete":
                    if not request.key:
                        raise HTTPException(status_code=400, detail="Key required for delete operation")
                    
                    deleted = await context_store.delete_scratchpad(request.session_id, request.key)
                    if deleted:
                        session.info.context_entries = max(0, session.info.context_entries - 1)
                    
                    return ContextResponse(
                        session_id=request.session_id,
                        operation=request.operation,
                        success=True,
                        data={"deleted": deleted}
                    )
                
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported operation: {request.operation}")
                    
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Context operation failed: {e}")
            return ContextResponse(
                session_id=request.session_id,
                operation=request.operation,
                success=False,
                error=str(e)
            )
    
    @app.get("/sessions/{session_id}/stats")
    async def get_session_stats(
        session_id: str,
        sm: SessionManager = Depends(get_session_manager)
    ):
        """Get session statistics"""
        try:
            async with sm.session_context(session_id) as session:
                return {
                    "session_id": session_id,
                    "status": session.info.status,
                    "created_at": session.info.created_at,
                    "last_activity": session.info.last_activity,
                    "total_requests": session.info.total_requests,
                    "total_collaborations": session.info.total_collaborations,
                    "context_entries": session.info.context_entries,
                    "active_collaborations": len(session.collaborations)
                }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Failed to get session stats {session_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def _execute_collaboration(session, collaboration_id: str, team_config_path: str, task: str):
    """Execute a collaboration in the background"""
    try:
        # Create team manager for this collaboration
        team_manager = session.create_team_manager(team_config_path)
        
        # Execute collaboration
        result = await team_manager.collaborate(team_config_path, task)
        
        await session.complete_collaboration(collaboration_id, result)
        logger.info(f"Collaboration {collaboration_id} completed successfully")
        
    except Exception as e:
        await session.complete_collaboration(collaboration_id, None, str(e))
        logger.error(f"Collaboration {collaboration_id} failed: {e}")


async def _stream_collaboration(session, collaboration_id: str, team_config_path: str, task: str) -> AsyncGenerator[str, None]:
    """Stream collaboration events"""
    try:
        # Create team manager for this collaboration
        team_manager = session.create_team_manager(team_config_path)
        
        # Stream events from the collaboration
        async for event in team_manager.stream_collaborate(team_config_path, task):
            event_data = {
                "collaboration_id": collaboration_id,
                "event": event,
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(event_data)
        
        # Mark as completed
        await session.complete_collaboration(collaboration_id, {"status": "completed"})
        
        # Send completion event
        completion_event = {
            "collaboration_id": collaboration_id,
            "event": {"type": "completed"},
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(completion_event)
        
    except Exception as e:
        await session.complete_collaboration(collaboration_id, None, str(e))
        
        # Send error event
        error_event = {
            "collaboration_id": collaboration_id,
            "event": {"type": "error", "error": str(e)},
            "timestamp": datetime.now().isoformat()
        }
        yield json.dumps(error_event)


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