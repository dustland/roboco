"""
Modern Web Interface for Roboco Observability

FastAPI + HTMX + Jinja2 + TailwindCSS + Preline UI
A beautiful, responsive web dashboard for monitoring Roboco tasks, events, and memory.
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

# Global variable to store data_dir for the web app
_web_app_data_dir: Optional[str] = None

# Pydantic models for API requests
class ChangeDataDirectoryRequest(BaseModel):
    path: str

def create_web_app(data_dir: Optional[str] = None) -> FastAPI:
    """Create the FastAPI web application."""
    global _web_app_data_dir
    _web_app_data_dir = data_dir
    
    app = FastAPI(
        title="Roboco Observability Dashboard",
        description="Modern web interface for Roboco observability",
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
        return get_monitor(_web_app_data_dir)
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Main dashboard page."""
        dashboard_data = monitor.get_dashboard_data()
        return templates.TemplateResponse("dashboard.jinja2", {
            "request": request,
            "dashboard_data": dashboard_data,
            "page_title": "Dashboard"
        })
    
    @app.get("/tasks", response_class=HTMLResponse)
    async def tasks_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Tasks page."""
        recent_tasks = monitor.get_recent_tasks(20)
        return templates.TemplateResponse("tasks.jinja2", {
            "request": request,
            "recent_tasks": recent_tasks,
            "page_title": "Tasks"
        })
    
    @app.get("/events", response_class=HTMLResponse)
    async def events_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Events page."""
        event_summary = monitor.get_event_summary() if monitor.is_integrated else {}
        return templates.TemplateResponse("events.jinja2", {
            "request": request,
            "event_summary": event_summary,
            "is_integrated": monitor.is_integrated,
            "page_title": "Events"
        })
    
    @app.get("/memory", response_class=HTMLResponse)
    async def memory_page(request: Request, monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Memory page."""
        categories = monitor.get_memory_categories()
        return templates.TemplateResponse("memory.jinja2", {
            "request": request,
            "categories": categories,
            "page_title": "Memory"
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
        return templates.TemplateResponse("messages.jinja2", {
            "request": request,
            "all_tasks": all_tasks,
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
        if not monitor.is_integrated:
            return {"events": [], "error": "Events only available in integrated mode"}
        
        events = monitor.get_events(event_type, limit)
        return {"events": events}
    
    @app.get("/api/memory/search")
    async def search_memory(
        q: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Search memory."""
        results = monitor.search_memory(q)
        return {"results": results}
    
    @app.get("/api/memory/category/{category}")
    async def memory_by_category(
        category: str,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Get memory by category."""
        memory_data = monitor.get_memory_by_category(category)
        return {"memory_data": memory_data}
    
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
        """Get full conversation for a task (alias for task conversation)."""
        conversation = monitor.get_task_conversation(task_id)
        return {
            "task_id": task_id,
            "conversation": conversation,
            "message_count": len(conversation)
        }
    
    @app.post("/api/monitor/start")
    async def start_monitor(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Start the monitor."""
        monitor.start()
        return {"status": "started"}
    
    @app.post("/api/monitor/stop")
    async def stop_monitor(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Stop the monitor."""
        monitor.stop()
        return {"status": "stopped"}
    
    @app.post("/api/monitor/refresh")
    async def refresh_monitor(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Refresh monitor data."""
        try:
            await monitor.refresh_data()
            return {"status": "refreshed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Data Directory Management APIs
    @app.get("/api/data-directory/info")
    async def get_data_directory_info(monitor: ObservabilityMonitor = Depends(get_monitor_dependency)):
        """Get information about the current data directory."""
        try:
            from pathlib import Path
            import os
            from datetime import datetime
            
            data_dir = Path(monitor.data_dir)
            
            if not data_dir.exists():
                return {
                    "exists": False,
                    "path": str(data_dir),
                    "file_count": 0,
                    "size_mb": 0,
                    "last_modified": None
                }
            
            # Count files and calculate size
            files = list(data_dir.glob("*.json"))
            total_size = sum(f.stat().st_size for f in files if f.is_file())
            size_mb = round(total_size / (1024 * 1024), 2)
            
            # Get last modified time
            last_modified = None
            if files:
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            return {
                "exists": True,
                "path": str(data_dir),
                "file_count": len(files),
                "size_mb": size_mb,
                "last_modified": last_modified,
                "files": [f.name for f in files]
            }
            
        except Exception as e:
            return {"error": str(e), "exists": False}
    
    @app.post("/api/data-directory/change")
    async def change_data_directory(
        request: ChangeDataDirectoryRequest,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Change the data directory."""
        try:
            from pathlib import Path
            
            new_path = request.path.strip()
            if not new_path:
                return {"success": False, "error": "Path is required"}
            
            new_data_dir = Path(new_path)
            
            # Validate the path
            if not new_data_dir.is_absolute():
                # Make it absolute relative to current working directory
                new_data_dir = Path.cwd() / new_data_dir
            
            # Create directory if it doesn't exist
            try:
                new_data_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return {"success": False, "error": f"Cannot create directory: {str(e)}"}
            
            # Check if we can write to the directory
            test_file = new_data_dir / ".test_write"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                return {"success": False, "error": f"Cannot write to directory: {str(e)}"}
            
            # Update the global monitor instance to use the new data directory
            global _web_app_data_dir
            _web_app_data_dir = str(new_data_dir)
            
            # Note: In a real implementation, you might want to:
            # 1. Stop the current monitor
            # 2. Create a new monitor with the new data directory
            # 3. Restart the monitor
            # For now, we'll just update the path and let the user reload
            
            return {
                "success": True, 
                "message": f"Data directory changed to {new_data_dir}",
                "new_path": str(new_data_dir)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/data-directory/browse")
    async def browse_data_directory(
        path: Optional[str] = None,
        monitor: ObservabilityMonitor = Depends(get_monitor_dependency)
    ):
        """Browse directories for data directory selection."""
        try:
            from pathlib import Path
            import os
            
            if path:
                browse_path = Path(path)
            else:
                browse_path = Path.cwd()
            
            if not browse_path.exists() or not browse_path.is_dir():
                browse_path = Path.cwd()
            
            # Get directories only
            directories = []
            try:
                for item in browse_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        directories.append({
                            "name": item.name,
                            "path": str(item),
                            "is_roboco_data": item.name == "roboco_data" or (item / "conversations.json").exists()
                        })
            except PermissionError:
                pass
            
            # Sort directories
            directories.sort(key=lambda x: x["name"].lower())
            
            return {
                "current_path": str(browse_path),
                "parent_path": str(browse_path.parent) if browse_path.parent != browse_path else None,
                "directories": directories
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    return app


def run_web_app(host: str = "0.0.0.0", port: int = 8501, data_dir: Optional[str] = None):
    """Run the web application."""
    app = create_web_app(data_dir)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web_app() 