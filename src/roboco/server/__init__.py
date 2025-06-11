"""
RoboCo Server

Multi-user server implementation with session management and context isolation.
Each session gets its own isolated context store, event bus, and team instances.

Optional component - users can ignore this if they want direct framework access.
"""

from .session_manager import SessionManager, Session
from .api import create_app
from .models import SessionConfig, SessionInfo, SessionStatus

__all__ = [
    "SessionManager",
    "Session", 
    "create_app",
    "SessionConfig",
    "SessionInfo",
    "SessionStatus",
] 