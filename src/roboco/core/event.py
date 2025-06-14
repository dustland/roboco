"""
Event component for real-time event system.
"""

import asyncio
from ..utils.logger import get_logger
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from enum import Enum

logger = get_logger(__name__)


class EventType(Enum):
    """Standard event types."""
    AGENT_CREATED = "agent.created"
    AGENT_ACTIVATED = "agent.activated"
    AGENT_DEACTIVATED = "agent.deactivated"
    AGENT_RESET = "agent.reset"
    
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    
    TOOL_EXECUTED = "tool.executed"
    TOOL_FAILED = "tool.failed"
    
    MEMORY_SAVED = "memory.saved"
    MEMORY_SEARCHED = "memory.searched"
    
    TEAM_CREATED = "team.created"
    TEAM_CONVERSATION_STARTED = "team.conversation.started"
    TEAM_CONVERSATION_ENDED = "team.conversation.ended"
    TEAM_SPEAKER_CHANGED = "team.speaker.changed"
    
    CUSTOM = "custom"


@dataclass
class Event:
    """A single event."""
    event_type: str
    data: Dict[str, Any]
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "event_id": self.event_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create from dictionary."""
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class EventBus:
    """Event bus for individual agents."""
    
    def __init__(self, agent: "Agent"):
        self.agent = agent
        self.listeners: Dict[str, List[Callable]] = {}
        self.event_history: List[Event] = []
        self.max_history = 1000
        
        logger.debug(f"Initialized event bus for agent '{agent.name}'")
    
    def on(self, event_type: str, callback: Callable[[Event], None]):
        """Register an event listener."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(callback)
        logger.debug(f"Registered listener for '{event_type}' on agent '{self.agent.name}'")
    
    def off(self, event_type: str, callback: Callable[[Event], None]):
        """Unregister an event listener."""
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(callback)
                logger.debug(f"Unregistered listener for '{event_type}' on agent '{self.agent.name}'")
            except ValueError:
                pass
    
    def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event."""
        event = Event(
            event_type=event_type,
            data=data,
            source=self.agent.name
        )
        
        # Add to history
        self.event_history.append(event)
        self._cleanup_history()
        
        # Notify listeners
        listeners = self.listeners.get(event_type, [])
        for callback in listeners:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Event listener failed for '{event_type}': {e}")
        
        logger.debug(f"Emitted event '{event_type}' from agent '{self.agent.name}'")
    
    async def emit_async(self, event_type: str, data: Dict[str, Any]):
        """Emit an event asynchronously."""
        event = Event(
            event_type=event_type,
            data=data,
            source=self.agent.name
        )
        
        # Add to history
        self.event_history.append(event)
        self._cleanup_history()
        
        # Notify listeners asynchronously
        listeners = self.listeners.get(event_type, [])
        tasks = []
        
        for callback in listeners:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(event))
            else:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Event listener failed for '{event_type}': {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.debug(f"Emitted async event '{event_type}' from agent '{self.agent.name}'")
    
    def get_events(self, event_type: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history."""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:] if limit > 0 else events
    
    def get_recent_events(self, minutes: int = 60) -> List[Event]:
        """Get events from the last N minutes."""
        cutoff = datetime.now().timestamp() - (minutes * 60)
        return [
            e for e in self.event_history 
            if e.timestamp.timestamp() > cutoff
        ]
    
    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
        logger.debug(f"Cleared event history for agent '{self.agent.name}'")
    
    def _cleanup_history(self):
        """Clean up old events."""
        if len(self.event_history) > self.max_history:
            excess = len(self.event_history) - self.max_history
            self.event_history = self.event_history[excess:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        if not self.event_history:
            return {
                "total_events": 0,
                "event_types": {},
                "oldest_event": None,
                "newest_event": None
            }
        
        # Count events by type
        event_types = {}
        for event in self.event_history:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        return {
            "total_events": len(self.event_history),
            "event_types": event_types,
            "oldest_event": min(self.event_history, key=lambda e: e.timestamp).timestamp.isoformat(),
            "newest_event": max(self.event_history, key=lambda e: e.timestamp).timestamp.isoformat(),
            "active_listeners": {et: len(listeners) for et, listeners in self.listeners.items()}
        }


class GlobalEventBus:
    """Global event bus for system-wide events."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.listeners = {}
            cls._instance.event_history = []
            cls._instance.max_history = 10000
        return cls._instance
    
    def on(self, event_type: str, callback: Callable[[Event], None]):
        """Register a global event listener."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        
        self.listeners[event_type].append(callback)
        logger.debug(f"Registered global listener for '{event_type}'")
    
    def off(self, event_type: str, callback: Callable[[Event], None]):
        """Unregister a global event listener."""
        if event_type in self.listeners:
            try:
                self.listeners[event_type].remove(callback)
                logger.debug(f"Unregistered global listener for '{event_type}'")
            except ValueError:
                pass
    
    def emit(self, event_type: str, data: Dict[str, Any], source: str = "system"):
        """Emit a global event."""
        event = Event(
            event_type=event_type,
            data=data,
            source=source
        )
        
        # Add to history
        self.event_history.append(event)
        self._cleanup_history()
        
        # Notify specific listeners
        listeners = self.listeners.get(event_type, [])
        
        # Also notify wildcard listeners
        wildcard_listeners = self.listeners.get("*", [])
        all_listeners = listeners + wildcard_listeners
        
        for callback in all_listeners:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Global event listener failed for '{event_type}': {e}")
        
        logger.debug(f"Emitted global event '{event_type}' from '{source}'")
    
    def _cleanup_history(self):
        """Clean up old events."""
        if len(self.event_history) > self.max_history:
            excess = len(self.event_history) - self.max_history
            self.event_history = self.event_history[excess:]


# Global event bus instance
global_events = GlobalEventBus() 