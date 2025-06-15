"""
Modern Web Interface for AgentX Observability

FastAPI + HTMX + Jinja2 + TailwindCSS + Preline UI
A beautiful, responsive web dashboard for monitoring AgentX project data.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

from .monitor import get_monitor, ObservabilityMonitor

# Global variable to store project_path for the web app
_web_app_project_path: Optional[str] = None

# Pydantic models for API requests
class ChangeProjectPathRequest(BaseModel):
    path: str

def create_web_app(project_path: Optional[str] = None) -> FastAPI:
    """Create the FastAPI web application."""
    global _web_app_project_path
    _web_app_project_path = project_path
    
    app = FastAPI(
        title="AgentX Observability Dashboard",
        description="Modern web interface for AgentX project observability",
        version="1.0.0"
    )
    
    # Set up templates and static files
    current_dir = Path(__file__).parent
    templates_dir = current_dir / "templates"
    static_dir = current_dir / "static"
    
    # Create directories if they don't exist
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    templates = Jinja2Templates(directory=str(templates_dir))
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Dependency to get monitor
    def get_monitor_dependency() -> ObservabilityMonitor:
        return get_monitor(_web_app_project_path)
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Main dashboard page."""
        dashboard_data = monitor.get_dashboard_data()
        config_data = monitor.get_configuration_data()
        return templates.TemplateResponse("dashboard.jinja2", {
            "request": request,
            "dashboard_data": dashboard_data,
            "config_data": config_data,
            "page_title": "Dashboard"
        })
    
    @app.get("/tasks", response_class=HTMLResponse)
    async def tasks_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Tasks page."""
        recent_tasks = monitor.get_recent_tasks(20)
        config_data = monitor.get_configuration_data()
        return templates.TemplateResponse("tasks.jinja2", {
            "request": request,
            "recent_tasks": recent_tasks,
            "config_data": config_data,
            "page_title": "Tasks"
        })
    
    @app.get("/events", response_class=HTMLResponse)
    async def events_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Events page."""
        event_stats = monitor.event_capture.get_event_stats()
        config_data = monitor.get_configuration_data()
        return templates.TemplateResponse("events.jinja2", {
            "request": request,
            "event_stats": event_stats,
            "config_data": config_data,
            "page_title": "Events"
        })
    
    @app.get("/artifacts", response_class=HTMLResponse)
    async def artifacts_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Artifacts page."""
        config_data = monitor.get_configuration_data()
        artifacts_data = {
            "files": monitor.get_artifacts_files(),
            "stats": monitor.get_artifacts_stats()
        }
        return templates.TemplateResponse("artifacts.jinja2", {
            "request": request,
            "config_data": config_data,
            "artifacts_data": artifacts_data,
            "page_title": "Artifacts"
        })
    
    @app.get("/configuration", response_class=HTMLResponse)
    async def configuration_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Configuration page."""
        config_data = monitor.get_configuration_data()
        return templates.TemplateResponse("configuration.jinja2", {
            "request": request,
            "config_data": config_data,
            "page_title": "Configuration"
        })
    
    @app.get("/messages", response_class=HTMLResponse)
    async def messages_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Messages page - conversation history between agents."""
        all_tasks = monitor.get_recent_tasks(50)  # Get more tasks for messages view
        config_data = monitor.get_configuration_data()
        return templates.TemplateResponse("messages.jinja2", {
            "request": request,
            "all_tasks": all_tasks,
            "config_data": config_data,
            "page_title": "Messages"
        })
    
    # HTMX API endpoints
    @app.get("/api/dashboard-stats")
    async def dashboard_stats(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get dashboard statistics for HTMX updates."""
        return monitor.get_dashboard_data()
    
    @app.get("/api/task/{task_id}/conversation")
    async def task_conversation(task_id: str, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get conversation history for a task."""
        conversation = monitor.get_task_conversation(task_id)
        return {"conversation": conversation}
    
    @app.get("/api/events")
    async def get_events(
        event_type: Optional[str] = None,
        limit: int = 100,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get events with optional filtering."""
        events = monitor.get_events(event_type, limit)
        return {"events": events}
    
    @app.get("/api/artifacts/files")
    async def get_artifacts_files(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get list of artifact files."""
        files = monitor.get_artifacts_files()
        return {"files": files}
    
    @app.get("/api/artifacts/file/{filename}")
    async def get_artifact_file(
        filename: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get artifact file content."""
        result = monitor.get_artifact_content(filename)
        return result
    
    @app.get("/api/artifacts/download/{filename}")
    async def download_artifact_file(
        filename: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Download artifact file."""
        from fastapi.responses import FileResponse
        try:
            file_path = monitor.storage._get_workspace_file_path(filename)
            if file_path.exists():
                return FileResponse(
                    path=str(file_path),
                    filename=filename,
                    media_type='application/octet-stream'
                )
            else:
                raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/messages/tasks")
    async def get_messages_tasks(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get all tasks for messages interface."""
        tasks = monitor.get_recent_tasks(100)  # Get more tasks for messages
        return {"tasks": tasks}
    
    @app.get("/api/messages/conversation/{task_id}")
    async def get_messages_conversation(
        task_id: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get full conversation for a task."""
        conversation = monitor.get_task_conversation(task_id)
        task_summary = monitor.conversation_history.get_task_summary(task_id)
        return {
            "task_id": task_id,
            "conversation": conversation,
            "message_count": len(conversation),
            "summary": task_summary
        }
    
    @app.get("/api/task/{task_id}/summary")
    async def get_task_summary(
        task_id: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get task summary information."""
        summary = monitor.conversation_history.get_task_summary(task_id)
        return {"task_id": task_id, "summary": summary}
    
    @app.get("/api/events/timerange")
    async def get_events_by_timerange(
        start_time: str,
        end_time: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get events within a time range."""
        # For now, just return recent events since we don't have time filtering implemented
        events = monitor.get_events(limit=1000)
        return {"events": events, "start_time": start_time, "end_time": end_time}
    
    @app.get("/api/artifacts/stats")
    async def get_artifacts_stats(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get artifacts statistics."""
        stats = monitor.get_artifacts_stats()
        return {"stats": stats}
    
    @app.post("/api/monitor/start")
    async def start_monitor(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Start the monitor."""
        monitor.start()
        return {"status": "started", "is_running": monitor.is_running}
    
    @app.post("/api/monitor/stop")
    async def stop_monitor(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Stop the monitor."""
        monitor.stop()
        return {"status": "stopped", "is_running": monitor.is_running}
    
    @app.post("/api/monitor/refresh")
    async def refresh_monitor(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Refresh monitor data."""
        monitor.refresh()
        return {"status": "refreshed", "last_refresh": monitor.last_refresh.isoformat() if monitor.last_refresh else None}
    
    # Project Directory Management APIs
    @app.get("/api/project/info")
    async def get_project_info(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get information about the current project."""
        try:
            project_status = monitor.get_project_status()
            return {
                "success": True,
                "project_status": project_status
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/project/change")
    async def change_project_path(
        request: ChangeProjectPathRequest,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Change the project path."""
        try:
            from pathlib import Path
            
            new_path = request.path.strip()
            if not new_path:
                return {"success": False, "error": "Path is required"}
            
            new_project_path = Path(new_path)
            
            # Validate the path
            if not new_project_path.is_absolute():
                # Make it absolute relative to current working directory
                new_project_path = Path.cwd() / new_project_path
            
            # Check if it's a valid project directory
            workspace_dir = new_project_path / "workspace"
            config_dir = new_project_path / "config"
            
            if not new_project_path.exists():
                return {"success": False, "error": f"Project directory does not exist: {new_project_path}"}
            
            if not workspace_dir.exists():
                return {"success": False, "error": f"Workspace directory not found: {workspace_dir}"}
            
            if not config_dir.exists():
                return {"success": False, "error": f"Config directory not found: {config_dir}"}
            
            # Update the global project path and recreate monitor
            global _web_app_project_path
            _web_app_project_path = str(new_project_path)
            
            # Force recreation of monitor with new path
            from .monitor import get_monitor
            if hasattr(get_monitor, '_instance'):
                delattr(get_monitor, '_instance')
            
            # Create new monitor instance with the new path
            new_monitor = get_monitor(str(new_project_path))
            
            return {
                "success": True, 
                "message": f"Project path changed to {new_project_path}",
                "new_path": str(new_project_path)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/config/files")
    async def get_config_files(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get list of configuration files."""
        try:
            files = monitor.get_config_files()
            return {"success": True, "files": files}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/config/file/{filename}")
    async def get_config_file(
        filename: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get specific configuration file content."""
        try:
            content = monitor.get_config_file(filename)
            file_info = monitor.config_viewer.get_config_file_info(filename)
            return {
                "success": True,
                "filename": filename,
                "content": content,
                "file_info": file_info
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return app


def run_web_app(host: str = "0.0.0.0", port: int = 8501, project_path: Optional[str] = None):
    """Run the web application."""
    app = create_web_app(project_path)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web_app() 