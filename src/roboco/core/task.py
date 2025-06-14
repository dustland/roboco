"""
Task management system for multi-agent collaboration.

This module provides the main Task class and related functionality for managing
collaborative tasks with teams of agents.

This is a backwards compatibility layer that wraps our new elegant architecture.
"""

import json
import uuid
import secrets
import string
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .team import Team, TeamConfig, create_team
from .agent import Agent, create_assistant_agent
from .memory import Memory
from .event import EventBus, Event
from .brain import ChatHistory
from ..utils.id import generate_short_id

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    CREATED = "created"
    RUNNING = "running"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"



@dataclass
class TaskConfig:
    """Task configuration."""
    name: str
    description: str = ""
    max_iterations: int = 10
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class TaskInfo:
    """Information about a task."""
    task_id: str
    description: str
    config_path: str
    status: str  # 'created', 'running', 'stopped', 'completed', 'failed'
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class ChatSession:
    """Handles chat interactions for a task."""
    
    def __init__(self, task: 'Task'):
        self.task = task
        self._history: List[Dict[str, Any]] = []
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """Get the chat history for this task."""
        return self._history.copy()
    
    async def send_message(self, message: str, sender: Optional[str] = None) -> Dict[str, Any]:
        """Send a message to the task collaboration."""
        if self.task.status != 'running':
            raise RuntimeError(f"Cannot send message to task with status: {self.task.status}")
        
        # Add message to history
        msg_entry = {
            "timestamp": datetime.now().isoformat(),
            "sender": sender or "user",
            "message": message,
            "type": "user_message"
        }
        self._history.append(msg_entry)
        
        return {"success": True, "message_id": len(self._history)}


@dataclass
class TaskResult:
    """Result of a completed task."""
    success: bool
    summary: str
    conversation_history: ChatHistory


class Task:
    """
    Main Task class for managing multi-agent collaboration.
    
    This is a backwards compatibility wrapper around our new elegant architecture.
    """
    
    def __init__(self, config: Union[TaskConfig, Dict[str, Any]], config_path: Optional[str] = None):
        """Initialize a task."""
        # Convert dict to config if needed
        if isinstance(config, dict):
            config = TaskConfig(**config)
        
        self.config = config
        self.description = config.description
        self.status: str = "created"
        
        # Generate a short, URL-friendly ID
        self.task_id = generate_short_id()
        
        self.config_path = config_path or ""
        self.created_at = datetime.now()
        self.updated_at = self.created_at
        self.metadata: Dict[str, Any] = config.metadata.copy()
        
        # Internal components
        self._team: Optional[Team] = None
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # API components
        self._chat_session: Optional[ChatSession] = None
    
    def _update_status(self, status: str):
        """Update task status and save state."""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.now()
        
        # Call registered handlers for status change
        self._call_handlers("task.status_changed", {
            "task_id": self.task_id,
            "old_status": old_status,
            "new_status": status,
            "timestamp": self.updated_at
        })
    
    def _call_handlers(self, event_type: str, data: Dict[str, Any]):
        """Call registered event handlers."""
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler({"event_type": event_type, "data": data})
            except Exception as e:
                print(f"Warning: Event handler failed: {e}")
    
    async def start(self, description: Optional[str] = None) -> 'TaskResult':
        """Start or resume the task collaboration."""
        if description:
            self.description = description
        
        # Update status
        self._update_status('running')
        
        try:
            # Initialize team if not already done
            if not self._team:
                # Create a simple team with one assistant agent for backwards compatibility
                agent = create_assistant_agent(
                    name="Assistant",
                    system_message=f"You are helping with: {self.description}"
                )
                
                self._team = create_team(
                    name=self.config.name,
                    agents=[agent],
                    max_rounds=self.config.max_iterations
                )
            
            # Initialize chat session
            if not self._chat_session:
                self._chat_session = ChatSession(self)
            
            # Call start handlers
            self._call_handlers("task.started", {
                "task_id": self.task_id,
                "description": self.description,
                "timestamp": datetime.now().isoformat()
            })
            
            # Run the collaboration
            chat_history = await self._team.start_conversation(
                initial_message=self.description
            )
            
            summary = f"Task completed: {self.description}"
            if chat_history.messages:
                # A simple summary from the last message
                summary = chat_history.messages[-1].content

            # Create and return a TaskResult
            result = TaskResult(
                success=True,
                summary=summary,
                conversation_history=chat_history
            )

            self._update_status('completed')
            self._call_handlers("task.completed", asdict(result))

            return result
            
        except Exception as e:
            logger.error(f"Task failed: {e}", exc_info=True)
            self._update_status('failed')
            self._call_handlers("task.failed", {"error": str(e)})
            
            return TaskResult(
                success=False,
                summary=f"Task failed: {e}",
                conversation_history=self._team.chat_history if self._team else ChatHistory()
            )
    
    def stop(self) -> bool:
        """Stop the task if it is running."""
        if self.status != 'running':
            return False
        
        self._update_status('stopped')
        
        # Call stop handlers
        self._call_handlers("task.stopped", {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def delete(self) -> bool:
        """Delete the task."""
        self._update_status('deleted')
        
        # Call delete handlers
        self._call_handlers("task.deleted", {
            "task_id": self.task_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Clean up
        if self._team:
            self._team.reset()
        
        return True
    
    def on(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Register an event handler."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable[[Dict[str, Any]], None]):
        """Unregister an event handler."""
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
            except ValueError:
                pass
    
    def get_chat(self) -> ChatSession:
        """Get the chat session for this task."""
        if not self._chat_session:
            self._chat_session = ChatSession(self)
        return self._chat_session
    
    def get_info(self) -> TaskInfo:
        """Get task information."""
        return TaskInfo(
            task_id=self.task_id,
            description=self.description,
            config_path=self.config_path,
            status=self.status,
            created_at=self.created_at.isoformat(),
            updated_at=self.updated_at.isoformat(),
            metadata=self.metadata
        )
    
    def get_memory(self):
        """Get memory interface for backwards compatibility."""
        # Simple mock memory for demo purposes
        class MockMemory:
            def get_all(self, limit=None):
                return []  # Return empty list for now
        
        return MockMemory()


# Global task registry for backwards compatibility
_task_registry: Dict[str, Task] = {}


def create_task(config_path: str, description: str = "") -> Task:
    """Create a new task."""
    config = TaskConfig(
        name=f"Task-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        description=description
    )
    
    task = Task(config, config_path)
    _task_registry[task.task_id] = task
    
    return task


def get_task(task_id: str, config_path: Optional[str] = None) -> Optional[Task]:
    """Get a task by ID."""
    return _task_registry.get(task_id)


def list_tasks() -> List[Task]:
    """List all tasks."""
    return list(_task_registry.values())