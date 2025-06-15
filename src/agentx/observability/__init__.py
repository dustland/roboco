"""
AgentX Observability Module

Project-based observability system providing:
1. Task-level conversation history from workspace data
2. Event capture from workspace files
3. Artifacts file browser and viewer for workspace files
4. Configuration viewing from config directory
5. Modern web interface with FastAPI + HTMX + TailwindCSS + Preline UI
6. Read-only monitoring of project data
"""

from .monitor import (
    ObservabilityMonitor, 
    ConversationHistory, 
    EventCapture, 
    ArtifactsViewer, 
    ConfigViewer,
    ProjectStorage,
    get_monitor,
    find_project_directory
)
from .web_app import create_web_app, run_web_app

__all__ = [
    "ObservabilityMonitor",
    "ConversationHistory", 
    "EventCapture",
    "ArtifactsViewer",
    "ConfigViewer",
    "ProjectStorage",
    "get_monitor",
    "find_project_directory",
    "create_web_app",
    "run_web_app"
] 