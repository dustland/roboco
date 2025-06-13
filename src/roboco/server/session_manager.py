"""
Session Manager

Manages isolated sessions with their own context stores, event buses, and team instances.
Provides session lifecycle management, cleanup, and resource isolation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from uuid import uuid4
import logging
from contextlib import asynccontextmanager

# TODO: Fix this import after server refactoring
# from roboco.memory.stores import InMemoryContextStore
from ..event.bus import InMemoryEventBus
from ..core.team_manager import TeamManager
from ..config.loaders import ConfigLoader
from .models import SessionInfo, SessionConfig, SessionStatus

logger = logging.getLogger(__name__)


class Session:
    """
    Isolated session containing its own context store, event bus, and team manager.
    """
    
    def __init__(self, session_info: SessionInfo, config: SessionConfig):
        self.info = session_info
        self.config = config
        
        # Isolated components for this session
        self.context_store = InMemoryContextStore()
        self.event_bus = InMemoryEventBus()
        # Note: TeamManager will be created per collaboration as it needs a config_path
        
        # Active collaborations
        self.collaborations: Dict[str, Any] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info(f"Created session {self.info.session_id}")
    
    async def update_activity(self):
        """Update last activity timestamp"""
        async with self._lock:
            self.info.last_activity = datetime.now()
            
    async def is_expired(self) -> bool:
        """Check if session has expired"""
        now = datetime.now()
        
        # Check idle timeout
        idle_time = now - self.info.last_activity
        if idle_time > self.config.max_idle_time:
            return True
            
        # Check total session timeout
        total_time = now - self.info.created_at
        if total_time > self.config.max_session_time:
            return True
            
        return False
    
    async def run(self, team_config_path: str, task: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Start a new collaboration in this session"""
        collaboration_id = str(uuid4())
        
        async with self._lock:
            # Load context if provided using scratchpad
            if context:
                for key, value in context.items():
                    await self.context_store.set_scratchpad(self.info.session_id, key, value)
            
            # Store collaboration info
            self.collaborations[collaboration_id] = {
                "id": collaboration_id,
                "team_config_path": team_config_path,
                "task": task,
                "status": "started",
                "created_at": datetime.now()
            }
            
            self.info.total_collaborations += 1
            await self.update_activity()
        
        logger.info(f"Started collaboration {collaboration_id} in session {self.info.session_id}")
        return collaboration_id
    
    async def get_collaboration(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        """Get collaboration info"""
        async with self._lock:
            return self.collaborations.get(collaboration_id)
    
    async def complete_collaboration(self, collaboration_id: str, result: Any, error: Optional[str] = None):
        """Mark collaboration as completed"""
        async with self._lock:
            if collaboration_id in self.collaborations:
                self.collaborations[collaboration_id].update({
                    "status": "completed" if error is None else "failed",
                    "result": result,
                    "error": error,
                    "completed_at": datetime.now()
                })
                await self.update_activity()
    
    def create_team_manager(self, team_config_path: str) -> 'TeamManager':
        """Create a TeamManager for this session with the given config"""
        # Create a custom TeamManager that uses this session's context and event stores
        team_manager = TeamManager(team_config_path, self.event_bus)
        
        # Replace the context store with our session-specific one
        team_manager.context_store = self.context_store
        
        return team_manager
    
    async def cleanup(self):
        """Cleanup session resources"""
        async with self._lock:
            # Clear context store for this session
            await self.context_store.clear_scratchpad_context(self.info.session_id)
            
            # Clear collaborations
            self.collaborations.clear()
            
            # Update status
            self.info.status = SessionStatus.TERMINATED
            
        logger.info(f"Cleaned up session {self.info.session_id}")


class SessionManager:
    """
    Manages multiple isolated sessions with automatic cleanup and resource management.
    """
    
    def __init__(self, default_config: Optional[SessionConfig] = None):
        self.default_config = default_config or SessionConfig()
        self.sessions: Dict[str, Session] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info("SessionManager initialized")
    
    async def start(self):
        """Start the session manager and cleanup task"""
        if self._running:
            return
            
        self._running = True
        if self.default_config.auto_cleanup:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("SessionManager started")
    
    async def stop(self):
        """Stop the session manager and cleanup all sessions"""
        if not self._running:
            return
            
        self._running = False
        
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Cleanup all sessions
        async with self._lock:
            for session in list(self.sessions.values()):
                await session.cleanup()
            self.sessions.clear()
        
        logger.info("SessionManager stopped")
    
    async def create_session(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None, config: Optional[SessionConfig] = None) -> SessionInfo:
        """Create a new session"""
        session_config = config or self.default_config
        
        session_info = SessionInfo(
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Set expiration time
        session_info.expires_at = session_info.created_at + session_config.max_session_time
        
        session = Session(session_info, session_config)
        
        async with self._lock:
            self.sessions[session_info.session_id] = session
        
        logger.info(f"Created session {session_info.session_id} for user {user_id}")
        return session_info
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        async with self._lock:
            session = self.sessions.get(session_id)
            
            if session:
                # Check if expired
                if await session.is_expired():
                    session.info.status = SessionStatus.EXPIRED
                    return session
                
                # Update activity
                await session.update_activity()
                session.info.total_requests += 1
                
                # Update status
                if session.info.status == SessionStatus.IDLE:
                    session.info.status = SessionStatus.ACTIVE
            
            return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        async with self._lock:
            session = self.sessions.pop(session_id, None)
            
            if session:
                await session.cleanup()
                logger.info(f"Deleted session {session_id}")
                return True
            
            return False
    
    async def list_sessions(self, user_id: Optional[str] = None, status: Optional[SessionStatus] = None) -> List[SessionInfo]:
        """List sessions with optional filtering"""
        async with self._lock:
            sessions = []
            
            for session in self.sessions.values():
                # Filter by user_id
                if user_id and session.info.user_id != user_id:
                    continue
                
                # Filter by status
                if status and session.info.status != status:
                    continue
                
                sessions.append(session.info)
            
            return sessions
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        async with self._lock:
            total_sessions = len(self.sessions)
            active_sessions = sum(1 for s in self.sessions.values() if s.info.status == SessionStatus.ACTIVE)
            idle_sessions = sum(1 for s in self.sessions.values() if s.info.status == SessionStatus.IDLE)
            expired_sessions = sum(1 for s in self.sessions.values() if s.info.status == SessionStatus.EXPIRED)
            
            total_collaborations = sum(s.info.total_collaborations for s in self.sessions.values())
            total_requests = sum(s.info.total_requests for s in self.sessions.values())
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "idle_sessions": idle_sessions,
                "expired_sessions": expired_sessions,
                "total_collaborations": total_collaborations,
                "total_requests": total_requests
            }
    
    async def _cleanup_loop(self):
        """Background task to cleanup expired sessions"""
        while self._running:
            try:
                await self._cleanup_expired_sessions()
                await asyncio.sleep(300)  # Check every 5 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _cleanup_expired_sessions(self):
        """Cleanup expired sessions"""
        expired_sessions = []
        
        async with self._lock:
            for session_id, session in list(self.sessions.items()):
                if await session.is_expired():
                    expired_sessions.append(session_id)
        
        # Cleanup expired sessions
        for session_id in expired_sessions:
            await self.delete_session(session_id)
            logger.info(f"Cleaned up expired session {session_id}")
    
    @asynccontextmanager
    async def session_context(self, session_id: str):
        """Context manager for session operations"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if session.info.status == SessionStatus.EXPIRED:
            raise ValueError(f"Session {session_id} has expired")
        
        try:
            yield session
        finally:
            # Mark as idle if no activity for a while
            now = datetime.now()
            if now - session.info.last_activity > timedelta(minutes=5):
                session.info.status = SessionStatus.IDLE 