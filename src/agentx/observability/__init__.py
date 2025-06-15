"""
AgentX Observability Module

Focused observability system providing:
1. Task-level conversation history (who did what)
2. All events capture with on("*", handler)  
3. Memory viewer by keys/categories
4. Modern web interface with FastAPI + HTMX + TailwindCSS + Preline UI
"""

from .monitor import ObservabilityMonitor, ConversationHistory, EventCapture, MemoryViewer, get_monitor
from .web_app import create_web_app, run_web_app

__all__ = [
    "ObservabilityMonitor",
    "ConversationHistory", 
    "EventCapture",
    "MemoryViewer",
    "get_monitor",
    "create_web_app",
    "run_web_app"
] 