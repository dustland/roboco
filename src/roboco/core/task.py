"""
Task management system for multi-agent collaboration.

This module provides the main Task class and related functionality for managing
collaborative tasks with teams of agents.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from pathlib import Path
from dataclasses import dataclass, asdict

from .team_manager import TeamManager
from .models import TaskResult
from .exceptions import ConfigurationError
from .memory import TaskMemory
from ..event.bus import InMemoryEventBus
from ..event.events import Event


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
        
        # TODO: Implement actual message sending to running collaboration
        # This would integrate with the team manager's group chat
        
        return {"success": True, "message_id": len(self._history)}


class Task:
    """
    Main Task class for managing multi-agent collaboration.
    
    This class provides the primary API for:
    - Task lifecycle management (start, stop, delete)
    - Event handling
    - Chat session access
    - Memory operations
    """
    
    def __init__(self, task_id: str, config_path: str, description: str = ""):
        """Initialize a task.
        
        Args:
            task_id: Unique task identifier
            config_path: Path to team configuration file
            description: Task description
        """
        self.task_id = task_id
        self.config_path = config_path
        self.description = description
        self.status = 'created'
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.metadata: Dict[str, Any] = {}
        
        # Internal components
        self._team_manager: Optional[TeamManager] = None
        self._memory: Optional[TaskMemory] = None
        self._event_bus = InMemoryEventBus()
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # API components
        self._chat_session: Optional[ChatSession] = None
        
        # Task persistence
        self._workspace_path = Path("./workspace")
        self._workspace_path.mkdir(exist_ok=True)
        self._task_file = self._workspace_path / f"task_{task_id}.json"
        
        # Initialize memory
        self._initialize_memory()
        
        # Save initial state
        self._save_state()
    
    def _initialize_memory(self):
        """Initialize the memory system."""
        try:
            from ..config.models import MemoryConfig
            memory_config = MemoryConfig()
            self._memory = TaskMemory(task_id=self.task_id, config=memory_config)
        except Exception as e:
            print(f"Warning: Could not initialize memory: {e}")
            self._memory = None
    
    def _save_state(self):
        """Save task state to disk."""
        state = {
            "task_id": self.task_id,
            "config_path": self.config_path,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata
        }
        
        try:
            with open(self._task_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save task state: {e}")
    
    def _load_state(self):
        """Load task state from disk."""
        if not self._task_file.exists():
            return
        
        try:
            with open(self._task_file, 'r') as f:
                state = json.load(f)
            
            self.description = state.get("description", "")
            self.status = state.get("status", "created")
            self.created_at = state.get("created_at", self.created_at)
            self.updated_at = state.get("updated_at", self.updated_at)
            self.metadata = state.get("metadata", {})
        except Exception as e:
            print(f"Warning: Could not load task state: {e}")
    
    def _update_status(self, status: str):
        """Update task status and save state."""
        old_status = self.status
        self.status = status
        self.updated_at = datetime.now().isoformat()
        self._save_state()
        
        # Emit status change event
        self._emit_event("task.status_changed", {
            "task_id": self.task_id,
            "old_status": old_status,
            "new_status": status,
            "timestamp": self.updated_at
        })
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit an event."""
        event = Event(event_type=event_type, data=data)
        self._event_bus.emit(event)
        
        # Call registered handlers
        handlers = self._event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Warning: Event handler failed: {e}")
    
    async def start(self, description: Optional[str] = None) -> TaskResult:
        """Start or resume the task collaboration.
        
        Args:
            description: Optional task description (updates existing if provided)
            
        Returns:
            TaskResult with the outcome
        """
        if description:
            self.description = description
        
        # Update status
        if self.status == 'created':
            self._update_status('running')
            action = "started"
        else:
            self._update_status('running')
            action = "resumed"
        
        try:
            # Initialize team manager if not already done
            if not self._team_manager:
                self._team_manager = TeamManager(
                    config_path=self.config_path,
                    event_bus=self._event_bus,
                    task_id=self.task_id
                )
            
            # Initialize chat session
            if not self._chat_session:
                self._chat_session = ChatSession(self)
            
            # Emit start event
            self._emit_event(f"task.{action}", {
                "task_id": self.task_id,
                "description": self.description,
                "timestamp": datetime.now().isoformat()
            })
            
            # Run the collaboration
            result = await self._team_manager.run(
                task=self.description,
                continue_task=(action == "resumed")
            )
            
            # Update status based on result
            if result.success:
                self._update_status('completed')
            else:
                self._update_status('failed')
            
            return result
            
        except Exception as e:
            self._update_status('failed')
            return TaskResult(
                success=False,
                summary=f"Task failed: {str(e)}",
                chat_history=[],
                participants=[],
                error_message=str(e),
                task_id=self.task_id
            )
    
    async def stop(self) -> bool:
        """Stop the running task.
        
        Returns:
            True if successfully stopped, False otherwise
        """
        if self.status != 'running':
            return False
        
        try:
            # TODO: Implement actual stopping of running collaboration
            # This would need to interrupt the team manager's group chat
            
            self._update_status('stopped')
            
            self._emit_event("task.stopped", {
                "task_id": self.task_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            print(f"Warning: Error stopping task: {e}")
            return False
    
    async def delete(self) -> bool:
        """Delete the task and clean up resources.
        
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            # Stop if running
            if self.status == 'running':
                await self.stop()
            
            # Clear memory if available
            if self._memory:
                self._memory.clear()
            
            # Remove task file
            if self._task_file.exists():
                self._task_file.unlink()
            
            # Remove from global task registry
            _remove_task_from_registry(self.task_id)
            
            self._emit_event("task.deleted", {
                "task_id": self.task_id,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            print(f"Warning: Error deleting task: {e}")
            return False
    
    def on(self, event_type: str, handler: Callable[[Event], None]):
        """Register an event handler.
        
        Args:
            event_type: Type of event to listen for
            handler: Function to call when event occurs
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def off(self, event_type: str, handler: Callable[[Event], None]):
        """Unregister an event handler.
        
        Args:
            event_type: Type of event to stop listening for
            handler: Function to remove
        """
        if event_type in self._event_handlers:
            try:
                self._event_handlers[event_type].remove(handler)
                if not self._event_handlers[event_type]:
                    del self._event_handlers[event_type]
            except ValueError:
                pass  # Handler not found
    
    def get_chat(self) -> ChatSession:
        """Get the chat session for this task."""
        if not self._chat_session:
            self._chat_session = ChatSession(self)
        return self._chat_session
    
    def get_memory(self) -> Optional[TaskMemory]:
        """Get the memory interface for this task."""
        return self._memory
    
    def get_info(self) -> TaskInfo:
        """Get task information."""
        return TaskInfo(
            task_id=self.task_id,
            description=self.description,
            config_path=self.config_path,
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
            metadata=self.metadata.copy()
        )
    
    @classmethod
    def load(cls, task_id: str) -> Optional['Task']:
        """Load an existing task from disk.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task instance if found, None otherwise
        """
        workspace_path = Path("./workspace")
        task_file = workspace_path / f"task_{task_id}.json"
        
        if not task_file.exists():
            return None
        
        try:
            with open(task_file, 'r') as f:
                state = json.load(f)
            
            task = cls(
                task_id=state["task_id"],
                config_path=state["config_path"],
                description=state.get("description", "")
            )
            
            # Load saved state
            task.status = state.get("status", "created")
            task.created_at = state.get("created_at", task.created_at)
            task.updated_at = state.get("updated_at", task.updated_at)
            task.metadata = state.get("metadata", {})
            
            # Add to registry
            _add_task_to_registry(task)
            
            return task
            
        except Exception as e:
            print(f"Warning: Could not load task {task_id}: {e}")
            return None


# Global task registry
_task_registry: Dict[str, Task] = {}


def _add_task_to_registry(task: Task):
    """Add task to global registry."""
    _task_registry[task.task_id] = task


def _remove_task_from_registry(task_id: str):
    """Remove task from global registry."""
    _task_registry.pop(task_id, None)


def create_task(config_path: str, description: str = "") -> Task:
    """Create a new task.
    
    Args:
        config_path: Path to team configuration file
        description: Task description
        
    Returns:
        New Task instance
    """
    task_id = _generate_task_id()
    task = Task(task_id=task_id, config_path=config_path, description=description)
    _add_task_to_registry(task)
    return task


def get_task(task_id: str) -> Optional[Task]:
    """Get an existing task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task instance if found, None otherwise
    """
    # Check registry first
    if task_id in _task_registry:
        return _task_registry[task_id]
    
    # Try to load from disk
    task = Task.load(task_id)
    return task


def list_tasks() -> List[Task]:
    """List all tasks.
    
    Returns:
        List of all Task instances
    """
    # Load all tasks from workspace
    workspace_path = Path("./workspace")
    if not workspace_path.exists():
        return []
    
    tasks = []
    for task_file in workspace_path.glob("task_*.json"):
        task_id = task_file.stem.replace("task_", "")
        task = get_task(task_id)
        if task:
            tasks.append(task)
    
    return tasks


def _generate_task_id() -> str:
    """Generate a unique task ID."""
    return str(uuid.uuid4())[:8]