"""
Event system for AgentX framework.

This package provides a comprehensive event bus system for publish/subscribe
patterns, enabling proper observability and monitoring.
"""

from .bus import EventBus, get_event_bus, initialize_event_bus
from .types import Event, EventHandler, EventFilter, EventPriority
from .middleware import EventMiddleware, LoggingMiddleware, MetricsMiddleware
from .subscribers import EventSubscriber, AsyncEventSubscriber
from .api import (
    publish_event, publish_event_sync, subscribe_to_events, unsubscribe_from_events, 
    get_event_stats, get_active_subscriptions, get_event_system_health,
    publish_task_event, publish_agent_event, publish_tool_event
)

__all__ = [
    # Core event bus (for advanced usage)
    'EventBus',
    'get_event_bus',
    'initialize_event_bus',
    
    # Simple API (recommended for most use cases)
    'publish_event',
    'publish_event_sync',
    'subscribe_to_events', 
    'unsubscribe_from_events',
    'get_event_stats',
    'get_active_subscriptions',
    'get_event_system_health',
    
    # Convenience functions
    'publish_task_event',
    'publish_agent_event', 
    'publish_tool_event',
    
    # Types and interfaces
    'Event',
    'EventHandler',
    'EventFilter',
    'EventPriority',
    
    # Middleware and subscribers
    'EventMiddleware',
    'LoggingMiddleware',
    'MetricsMiddleware',
    'EventSubscriber',
    'AsyncEventSubscriber',
] 