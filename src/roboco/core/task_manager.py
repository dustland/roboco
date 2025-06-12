"""
Task Management System

Handles task ID generation, session tracking, and continuation capabilities
for multi-agent collaborations.
"""

import json
import os
import random
import string
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

@dataclass
class TaskSession:
    """Represents a task session with metadata."""
    task_id: str
    task_description: str
    created_at: str
    updated_at: str
    status: str  # 'active', 'completed', 'paused', 'failed'
    config_path: str
    max_rounds: int
    current_round: int
    metadata: Dict[str, Any]
    conversation_context: Optional[List[Dict[str, Any]]] = None  # Store chat history
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskSession':
        return cls(**data)


class TaskManager:
    """
    Manages task sessions, IDs, and continuation capabilities.
    """
    
    def __init__(self, workspace_path: str = "./workspace"):
        """Initialize task manager with workspace path."""
        self.workspace_path = Path(workspace_path)
        self.sessions_file = self.workspace_path / "task_sessions.json"
        self.workspace_path.mkdir(exist_ok=True)
        self._sessions: Dict[str, TaskSession] = {}
        self._load_sessions()
    
    def _load_sessions(self):
        """Load existing task sessions from disk."""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    data = json.load(f)
                    self._sessions = {
                        task_id: TaskSession.from_dict(session_data)
                        for task_id, session_data in data.items()
                    }
            except Exception as e:
                print(f"Warning: Could not load task sessions: {e}")
                self._sessions = {}
    
    def _save_sessions(self):
        """Save task sessions to disk."""
        try:
            with open(self.sessions_file, 'w') as f:
                data = {
                    task_id: session.to_dict()
                    for task_id, session in self._sessions.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save task sessions: {e}")
    
    def _generate_task_id(self) -> str:
        """Generate a short, URL-friendly task ID."""
        # Use alphanumeric characters (A-Z, a-z, 0-9) and underscore
        chars = string.ascii_letters + string.digits + '_'
        
        # Generate until we get a unique ID
        max_attempts = 100
        for _ in range(max_attempts):
            task_id = ''.join(random.choices(chars, k=8))
            if task_id not in self._sessions:
                return task_id
        
        # Fallback: add random suffix if we can't find unique ID
        base_id = ''.join(random.choices(chars, k=6))
        suffix = ''.join(random.choices(string.digits, k=2))
        return base_id + suffix
    
    def create_task(
        self,
        task_description: str,
        config_path: str,
        max_rounds: int = 50,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new task session.
        
        Args:
            task_description: Description of the task
            config_path: Path to the team configuration
            max_rounds: Maximum rounds for the collaboration
            metadata: Optional metadata for the task
            
        Returns:
            Task ID for the new session
        """
        task_id = self._generate_task_id()
        now = datetime.now().isoformat()
        
        session = TaskSession(
            task_id=task_id,
            task_description=task_description,
            created_at=now,
            updated_at=now,
            status='active',
            config_path=config_path,
            max_rounds=max_rounds,
            current_round=0,
            metadata=metadata or {}
        )
        
        self._sessions[task_id] = session
        self._save_sessions()
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[TaskSession]:
        """Get a task session by ID."""
        return self._sessions.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        current_round: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        conversation_context: Optional[List[Dict[str, Any]]] = None
    ):
        """Update a task session."""
        if task_id not in self._sessions:
            return False
        
        session = self._sessions[task_id]
        session.updated_at = datetime.now().isoformat()
        
        if status:
            session.status = status
        if current_round is not None:
            session.current_round = current_round
        if metadata:
            session.metadata.update(metadata)
        if conversation_context is not None:
            session.conversation_context = conversation_context
        
        self._save_sessions()
        return True
    
    def save_conversation_progress(
        self,
        task_id: str,
        chat_history: List[Dict[str, Any]],
        current_round: Optional[int] = None
    ):
        """Save conversation progress incrementally."""
        if task_id not in self._sessions:
            return False
        
        session = self._sessions[task_id]
        session.conversation_context = chat_history
        session.updated_at = datetime.now().isoformat()
        
        if current_round is not None:
            session.current_round = current_round
        
        # Update status based on progress
        if current_round and current_round >= session.max_rounds:
            session.status = 'paused'  # Reached max rounds, can be resumed
            session.metadata['paused_reason'] = 'max_rounds_reached'
        
        self._save_sessions()
        return True
    
    def get_conversation_context(self, task_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the conversation context for a task."""
        session = self._sessions.get(task_id)
        return session.conversation_context if session else None
    
    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[TaskSession]:
        """List task sessions with optional filtering."""
        sessions = list(self._sessions.values())
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        return sessions[:limit]
    
    def find_continuable_tasks(
        self,
        task_description: str,
        similarity_threshold: float = 0.7
    ) -> List[TaskSession]:
        """
        Find tasks that can be continued based on description similarity.
        
        Args:
            task_description: Description to match against
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of potentially continuable tasks
        """
        # Simple keyword-based matching for now
        # In a production system, you'd use semantic similarity
        keywords = set(task_description.lower().split())
        
        continuable = []
        for session in self._sessions.values():
            if session.status in ['active', 'paused']:
                session_keywords = set(session.task_description.lower().split())
                overlap = len(keywords & session_keywords)
                total = len(keywords | session_keywords)
                similarity = overlap / total if total > 0 else 0
                
                if similarity >= similarity_threshold:
                    continuable.append(session)
        
        return sorted(continuable, key=lambda s: s.updated_at, reverse=True)
    
    def get_task_memory_context(self, task_id: str) -> Dict[str, Any]:
        """Get memory context for a task (task_id, agent_id patterns)."""
        session = self.get_task(task_id)
        if not session:
            return {}
        
        return {
            "task_id": task_id,
            "task_description": session.task_description,
            "created_at": session.created_at,
            "current_round": session.current_round,
            "metadata": session.metadata
        }
    
    def cleanup_old_tasks(self, days: int = 30):
        """Clean up task sessions older than specified days."""
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        to_remove = []
        for task_id, session in self._sessions.items():
            session_time = datetime.fromisoformat(session.updated_at).timestamp()
            if session_time < cutoff and session.status in ['completed', 'failed']:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._sessions[task_id]
        
        if to_remove:
            self._save_sessions()
            print(f"Cleaned up {len(to_remove)} old task sessions")
        
        return len(to_remove)
    
    def get_task_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a comprehensive summary of a task."""
        session = self.get_task(task_id)
        if not session:
            return None
        
        # Calculate progress percentage
        progress_pct = (session.current_round / session.max_rounds * 100) if session.max_rounds > 0 else 0
        
        # Calculate duration
        created = datetime.fromisoformat(session.created_at)
        updated = datetime.fromisoformat(session.updated_at)
        duration = updated - created
        
        return {
            "task_id": session.task_id,
            "description": session.task_description,
            "status": session.status,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "duration_seconds": duration.total_seconds(),
            "duration_human": self._format_duration(duration.total_seconds()),
            "progress": {
                "current_round": session.current_round,
                "max_rounds": session.max_rounds,
                "percentage": round(progress_pct, 1)
            },
            "config_path": session.config_path,
            "metadata": session.metadata
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m {int(seconds % 60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def list_tasks_detailed(
        self,
        status: Optional[str] = None,
        limit: int = 10,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List tasks with detailed information.
        
        Args:
            status: Optional status filter ('active', 'completed', 'paused', 'failed')
            limit: Maximum number of tasks to return
            include_metadata: Whether to include metadata in results
            
        Returns:
            List of detailed task information dictionaries
        """
        sessions = list(self._sessions.values())
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        # Convert to detailed summaries
        detailed_tasks = []
        for session in sessions[:limit]:
            summary = self.get_task_summary(session.task_id)
            if summary:
                if not include_metadata:
                    summary.pop('metadata', None)
                detailed_tasks.append(summary)
        
        return detailed_tasks
    
    def get_tasks_by_status_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get a summary of tasks grouped by status."""
        summary = {
            "active": {"count": 0, "tasks": []},
            "completed": {"count": 0, "tasks": []},
            "paused": {"count": 0, "tasks": []},
            "failed": {"count": 0, "tasks": []}
        }
        
        for session in self._sessions.values():
            status = session.status
            if status in summary:
                summary[status]["count"] += 1
                task_info = {
                    "task_id": session.task_id,
                    "description": session.task_description[:100] + "..." if len(session.task_description) > 100 else session.task_description,
                    "updated_at": session.updated_at,
                    "progress": f"{session.current_round}/{session.max_rounds}"
                }
                summary[status]["tasks"].append(task_info)
        
        # Sort tasks within each status by updated_at
        for status_info in summary.values():
            status_info["tasks"].sort(key=lambda x: x["updated_at"], reverse=True)
        
        return summary 