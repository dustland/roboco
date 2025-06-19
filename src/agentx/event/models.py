"""
Event subsystem models - Self-contained data models for event management.

This module contains all data models related to event management, following the
architectural rule that subsystems should be self-contained and not import from core.
"""

from typing import Dict, List, Optional, Any, Union, Literal, Callable, Awaitable
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

# Internal utilities (avoid importing from core/utils)
import secrets
import string

def generate_short_id(length: int = 8) -> str:
    """Generate a short, URL-friendly, cryptographically secure random ID."""
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============================================================================
# EVENT TYPE DEFINITIONS
# ============================================================================

class EventType(str, Enum):
    """Types of events in the system."""
    # Task lifecycle events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PAUSED = "task_paused"
    TASK_RESUMED = "task_resumed"
    
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    AGENT_HANDOFF = "agent_handoff"
    
    # Tool events
    TOOL_CALL_STARTED = "tool_call_started"
    TOOL_CALL_COMPLETED = "tool_call_completed"
    TOOL_CALL_FAILED = "tool_call_failed"
    TOOL_VALIDATION_ERROR = "tool_validation_error"
    
    # Memory events
    MEMORY_ADDED = "memory_added"
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_SYNTHESIZED = "memory_synthesized"
    
    # Storage events
    ARTIFACT_CREATED = "artifact_created"
    ARTIFACT_UPDATED = "artifact_updated"
    ARTIFACT_DELETED = "artifact_deleted"
    
    # System events
    SYSTEM_ERROR = "system_error"
    SYSTEM_WARNING = "system_warning"
    SYSTEM_INFO = "system_info"
    
    # Custom events
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventStatus(str, Enum):
    """Event processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


# ============================================================================
# CORE EVENT MODELS
# ============================================================================

class Event(BaseModel):
    """Base event model for the AgentX framework."""
    event_id: str = Field(default_factory=lambda: f"evt_{generate_short_id()}")
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str  # Component that generated the event
    
    # Event content
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Event context
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    # Event properties
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    correlation_id: Optional[str] = None
    parent_event_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "metadata": self.metadata,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "priority": self.priority.value,
            "status": self.status.value,
            "correlation_id": self.correlation_id,
            "parent_event_id": self.parent_event_id
        }


# ============================================================================
# SPECIFIC EVENT MODELS
# ============================================================================

class TaskEvent(Event):
    """Task-related events."""
    task_id: str
    event_type: Literal[
        EventType.TASK_STARTED,
        EventType.TASK_COMPLETED,
        EventType.TASK_FAILED,
        EventType.TASK_PAUSED,
        EventType.TASK_RESUMED
    ]


class TaskStartEvent(TaskEvent):
    """Event emitted when a task starts."""
    event_type: Literal[EventType.TASK_STARTED] = EventType.TASK_STARTED
    task_config: Dict[str, Any] = Field(default_factory=dict)
    initial_prompt: Optional[str] = None


class TaskCompleteEvent(TaskEvent):
    """Event emitted when a task completes."""
    event_type: Literal[EventType.TASK_COMPLETED] = EventType.TASK_COMPLETED
    result: Any = None
    execution_time_ms: float = 0.0
    total_rounds: int = 0


class TaskFailEvent(TaskEvent):
    """Event emitted when a task fails."""
    event_type: Literal[EventType.TASK_FAILED] = EventType.TASK_FAILED
    error: str
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None


class AgentEvent(Event):
    """Agent-related events."""
    agent_name: str
    event_type: Literal[
        EventType.AGENT_STARTED,
        EventType.AGENT_COMPLETED,
        EventType.AGENT_FAILED,
        EventType.AGENT_HANDOFF
    ]


class AgentStartEvent(AgentEvent):
    """Event emitted when an agent starts processing."""
    event_type: Literal[EventType.AGENT_STARTED] = EventType.AGENT_STARTED
    prompt: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)


class AgentCompleteEvent(AgentEvent):
    """Event emitted when an agent completes processing."""
    event_type: Literal[EventType.AGENT_COMPLETED] = EventType.AGENT_COMPLETED
    response: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_calls: List[str] = Field(default_factory=list)


class AgentHandoffEvent(AgentEvent):
    """Event emitted when an agent hands off to another agent."""
    event_type: Literal[EventType.AGENT_HANDOFF] = EventType.AGENT_HANDOFF
    from_agent: str
    to_agent: str
    handoff_reason: Optional[str] = None


class ToolEvent(Event):
    """Tool-related events."""
    tool_name: str
    event_type: Literal[
        EventType.TOOL_CALL_STARTED,
        EventType.TOOL_CALL_COMPLETED,
        EventType.TOOL_CALL_FAILED,
        EventType.TOOL_VALIDATION_ERROR
    ]


class ToolCallStartEvent(ToolEvent):
    """Event emitted when a tool call starts."""
    event_type: Literal[EventType.TOOL_CALL_STARTED] = EventType.TOOL_CALL_STARTED
    tool_call_id: str
    args: Dict[str, Any] = Field(default_factory=dict)


class ToolCallCompleteEvent(ToolEvent):
    """Event emitted when a tool call completes."""
    event_type: Literal[EventType.TOOL_CALL_COMPLETED] = EventType.TOOL_CALL_COMPLETED
    tool_call_id: str
    result: Any = None
    execution_time_ms: float = 0.0


class ToolCallFailEvent(ToolEvent):
    """Event emitted when a tool call fails."""
    event_type: Literal[EventType.TOOL_CALL_FAILED] = EventType.TOOL_CALL_FAILED
    tool_call_id: str
    error: str
    error_type: Optional[str] = None


class MemoryEvent(Event):
    """Memory-related events."""
    event_type: Literal[
        EventType.MEMORY_ADDED,
        EventType.MEMORY_RETRIEVED,
        EventType.MEMORY_SYNTHESIZED
    ]


class StorageEvent(Event):
    """Storage-related events."""
    event_type: Literal[
        EventType.ARTIFACT_CREATED,
        EventType.ARTIFACT_UPDATED,
        EventType.ARTIFACT_DELETED
    ]
    artifact_path: str


class SystemEvent(Event):
    """System-related events."""
    event_type: Literal[
        EventType.SYSTEM_ERROR,
        EventType.SYSTEM_WARNING,
        EventType.SYSTEM_INFO
    ]
    message: str
    component: Optional[str] = None


# ============================================================================
# EVENT HANDLER TYPES
# ============================================================================

EventHandler = Union[
    Callable[[Event], None],
    Callable[[Event], Awaitable[None]]
]

EventFilter = Callable[[Event], bool]


# ============================================================================
# EVENT SUBSCRIPTION MODELS
# ============================================================================

class EventSubscription(BaseModel):
    """Event subscription configuration."""
    subscription_id: str = Field(default_factory=lambda: f"sub_{generate_short_id()}")
    event_types: List[EventType]
    handler_name: str
    filter_expression: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventSubscriptionStats(BaseModel):
    """Statistics for event subscriptions."""
    subscription_id: str
    events_processed: int = 0
    events_failed: int = 0
    last_event_time: Optional[datetime] = None
    average_processing_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0


# ============================================================================
# EVENT BUS MODELS
# ============================================================================

class EventBusConfig(BaseModel):
    """Configuration for the event bus."""
    max_queue_size: int = 10000
    batch_size: int = 100
    flush_interval_ms: int = 1000
    retry_attempts: int = 3
    retry_delay_ms: int = 1000
    enable_persistence: bool = False
    persistence_path: Optional[str] = None


class EventBusStats(BaseModel):
    """Event bus statistics."""
    events_published: int = 0
    events_processed: int = 0
    events_failed: int = 0
    active_subscriptions: int = 0
    queue_size: int = 0
    average_processing_time_ms: float = 0.0
    uptime_seconds: float = 0.0


class EventBusHealth(BaseModel):
    """Event bus health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    queue_utilization: float  # 0.0 to 1.0
    processing_lag_ms: float
    error_rate: float  # 0.0 to 1.0
    last_event_time: Optional[datetime] = None
    warnings: List[str] = Field(default_factory=list)


# ============================================================================
# EVENT MIDDLEWARE MODELS
# ============================================================================

class EventMiddleware(ABC):
    """Abstract base class for event middleware."""
    
    @abstractmethod
    async def process_event(self, event: Event) -> Event:
        """Process an event and return the modified event."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get the middleware name."""
        pass


class EventMiddlewareConfig(BaseModel):
    """Configuration for event middleware."""
    name: str
    enabled: bool = True
    priority: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# EVENT LOGGING AND AUDIT MODELS
# ============================================================================

class EventLogEntry(BaseModel):
    """Event log entry for audit purposes."""
    log_id: str = Field(default_factory=lambda: f"log_{generate_short_id()}")
    event: Event
    processing_time_ms: float = 0.0
    handler_results: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    logged_at: datetime = Field(default_factory=datetime.now)


class EventAuditFilter(BaseModel):
    """Filter for event audit queries."""
    event_types: Optional[List[EventType]] = None
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    priority: Optional[EventPriority] = None
    time_range: Optional[tuple[datetime, datetime]] = None
    limit: int = 100
    offset: int = 0


# ============================================================================
# EVENT STREAMING MODELS
# ============================================================================

class EventStream(BaseModel):
    """Event stream configuration."""
    stream_id: str = Field(default_factory=lambda: f"stream_{generate_short_id()}")
    event_types: List[EventType]
    filter_expression: Optional[str] = None
    buffer_size: int = 1000
    batch_timeout_ms: int = 5000
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class EventBatch(BaseModel):
    """Batch of events for streaming."""
    batch_id: str = Field(default_factory=lambda: f"batch_{generate_short_id()}")
    events: List[Event]
    stream_id: str
    created_at: datetime = Field(default_factory=datetime.now)
    sequence_number: int = 0


# ============================================================================
# EVENT UTILITIES
# ============================================================================

def create_event(event_type: EventType, source: str, data: Dict[str, Any] = None,
                task_id: str = None, agent_name: str = None, tool_name: str = None,
                priority: EventPriority = EventPriority.NORMAL) -> Event:
    """Create a new event with the specified parameters."""
    return Event(
        event_type=event_type,
        source=source,
        data=data or {},
        task_id=task_id,
        agent_name=agent_name,
        tool_name=tool_name,
        priority=priority
    )


def create_task_start_event(task_id: str, source: str, task_config: Dict[str, Any] = None,
                           initial_prompt: str = None) -> TaskStartEvent:
    """Create a task start event."""
    return TaskStartEvent(
        task_id=task_id,
        source=source,
        task_config=task_config or {},
        initial_prompt=initial_prompt
    )


def create_tool_call_event(tool_name: str, tool_call_id: str, source: str,
                          args: Dict[str, Any] = None, task_id: str = None,
                          agent_name: str = None) -> ToolCallStartEvent:
    """Create a tool call start event."""
    return ToolCallStartEvent(
        tool_name=tool_name,
        tool_call_id=tool_call_id,
        source=source,
        args=args or {},
        task_id=task_id,
        agent_name=agent_name
    )


def create_agent_handoff_event(from_agent: str, to_agent: str, source: str,
                              task_id: str = None, handoff_reason: str = None) -> AgentHandoffEvent:
    """Create an agent handoff event."""
    return AgentHandoffEvent(
        agent_name=from_agent,
        from_agent=from_agent,
        to_agent=to_agent,
        source=source,
        task_id=task_id,
        handoff_reason=handoff_reason
    ) 