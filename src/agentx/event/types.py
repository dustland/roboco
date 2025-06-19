"""
Event system type definitions.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Awaitable, Union, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

# Import all event types from core.event
from .models import *

# Type definitions
EventHandler = Union[
    Callable[[Any], None],
    Callable[[Any], Awaitable[None]]
]

EventFilter = Callable[[Any], bool]

T = TypeVar('T', bound=BaseModel)


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventMetadata(BaseModel):
    """Metadata for events."""
    event_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3


class Event(BaseModel, Generic[T]):
    """Base event wrapper with metadata."""
    data: T
    metadata: EventMetadata
    
    @property
    def event_type(self) -> str:
        """Get the event type from the data."""
        if hasattr(self.data, 'type'):
            return self.data.type
        return self.data.__class__.__name__
    
    @property
    def event_id(self) -> str:
        """Get the event ID."""
        return self.metadata.event_id
    
    @property
    def timestamp(self) -> datetime:
        """Get the event timestamp."""
        return self.metadata.timestamp


class EventSubscription(BaseModel):
    """Event subscription configuration."""
    subscription_id: str
    event_types: List[str]
    handler: EventHandler
    filter_func: Optional[EventFilter] = None
    priority: EventPriority = EventPriority.NORMAL
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventBusStats(BaseModel):
    """Event bus statistics."""
    total_events_published: int = 0
    total_events_processed: int = 0
    total_events_failed: int = 0
    active_subscriptions: int = 0
    event_types_count: Dict[str, int] = Field(default_factory=dict)
    average_processing_time_ms: float = 0.0
    last_event_timestamp: Optional[datetime] = None 