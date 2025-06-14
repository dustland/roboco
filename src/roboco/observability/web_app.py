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
import uvicorn

from .monitor import get_monitor, ObservabilityMonitor


def create_web_app() -> FastAPI:
    """Create the FastAPI web application."""
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
        return get_monitor()
    
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
    
    return app


def run_web_app(host: str = "0.0.0.0", port: int = 8501):
    """Run the web application."""
    app = create_web_app()
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_web_app() 