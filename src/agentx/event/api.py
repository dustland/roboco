"""
Simple API for the AgentX event system.

This module provides clean, simple functions for event publishing and subscribing
without exposing the underlying event bus implementation.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .bus import get_event_bus
from .types import EventHandler, EventFilter, EventPriority, EventBusStats


async def publish_event(
    event_data: Any,
    event_type: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
    source: Optional[str] = None,
    correlation_id: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    Publish an event to the event system.
    
    Args:
        event_data: Event data (should be a Pydantic model)
        event_type: Optional event type override
        priority: Event priority (LOW, NORMAL, HIGH, CRITICAL)
        source: Event source identifier
        correlation_id: Correlation ID for tracing related events
        tags: Additional tags for filtering and categorization
        
    Returns:
        Event ID
        
    Example:
        ```python
        from agentx.event import publish_event
from .models import TaskStartEvent
        
        event_id = await publish_event(
            TaskStartEvent(
                task_id="task123",
                timestamp=datetime.now(),
                initial_prompt="Hello world",
                execution_mode="autonomous",
                team_config={}
            ),
            source="orchestrator",
            correlation_id="session_abc"
        )
        ```
    """
    event_bus = get_event_bus()
    return await event_bus.publish(
        event_data=event_data,
        event_type=event_type,
        priority=priority,
        source=source,
        correlation_id=correlation_id,
        tags=tags
    )


def publish_event_sync(
    event_data: Any,
    event_type: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
    source: Optional[str] = None,
    correlation_id: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    Synchronous wrapper for publish_event.
    
    Note: This creates a task but doesn't wait for it in sync context.
    Use publish_event() in async contexts for proper awaiting.
    
    Args:
        event_data: Event data (should be a Pydantic model)
        event_type: Optional event type override
        priority: Event priority (LOW, NORMAL, HIGH, CRITICAL)
        source: Event source identifier
        correlation_id: Correlation ID for tracing related events
        tags: Additional tags for filtering and categorization
        
    Returns:
        Event ID (or "pending" in async contexts)
    """
    event_bus = get_event_bus()
    return event_bus.publish_sync(
        event_data=event_data,
        event_type=event_type,
        priority=priority,
        source=source,
        correlation_id=correlation_id,
        tags=tags
    )


def subscribe_to_events(
    event_types: Union[str, List[str]],
    handler: EventHandler,
    filter_func: Optional[EventFilter] = None,
    priority: EventPriority = EventPriority.NORMAL,
    subscription_id: Optional[str] = None
) -> str:
    """
    Subscribe to events.
    
    Args:
        event_types: Event type(s) to subscribe to
        handler: Event handler function (sync or async)
        filter_func: Optional filter function to apply to events
        priority: Subscription priority (higher priority handlers run first)
        subscription_id: Optional custom subscription ID
        
    Returns:
        Subscription ID
        
    Example:
        ```python
        from agentx.event import subscribe_to_events
        
        def handle_task_events(event_data):
            print(f"Task event: {event_data.type}")
        
        subscription_id = subscribe_to_events(
            event_types=["event_task_start", "event_task_complete"],
            handler=handle_task_events,
            priority=EventPriority.HIGH
        )
        ```
    """
    event_bus = get_event_bus()
    return event_bus.subscribe(
        event_types=event_types,
        handler=handler,
        filter_func=filter_func,
        priority=priority,
        subscription_id=subscription_id
    )


def unsubscribe_from_events(subscription_id: str) -> bool:
    """
    Unsubscribe from events.
    
    Args:
        subscription_id: Subscription ID to remove
        
    Returns:
        True if subscription was found and removed
        
    Example:
        ```python
        from agentx.event import unsubscribe_from_events
        
        success = unsubscribe_from_events("my_subscription_123")
        if success:
            print("Successfully unsubscribed")
        ```
    """
    event_bus = get_event_bus()
    return event_bus.unsubscribe(subscription_id)


def get_event_stats() -> EventBusStats:
    """
    Get event system statistics.
    
    Returns:
        EventBusStats object with current statistics
        
    Example:
        ```python
        from agentx.event import get_event_stats
        
        stats = get_event_stats()
        print(f"Total events published: {stats.total_events_published}")
        print(f"Total events processed: {stats.total_events_processed}")
        print(f"Active subscriptions: {stats.active_subscriptions}")
        ```
    """
    event_bus = get_event_bus()
    return event_bus.get_stats()


def get_active_subscriptions() -> Dict[str, List[str]]:
    """
    Get current active subscriptions by event type.
    
    Returns:
        Dictionary mapping event types to lists of subscription IDs
        
    Example:
        ```python
        from agentx.event import get_active_subscriptions
        
        subscriptions = get_active_subscriptions()
        for event_type, sub_ids in subscriptions.items():
            print(f"{event_type}: {len(sub_ids)} subscribers")
        ```
    """
    event_bus = get_event_bus()
    return event_bus.get_subscriptions()


async def get_event_system_health() -> Dict[str, Any]:
    """
    Get event system health information.
    
    Returns:
        Dictionary with health information
        
    Example:
        ```python
        from agentx.event import get_event_system_health
        
        health = await get_event_system_health()
        print(f"Event system running: {health['running']}")
        print(f"Queue size: {health['queue_size']}")
        ```
    """
    event_bus = get_event_bus()
    return await event_bus.health_check()


# Convenience functions for common event types
async def publish_task_event(event_data: Any, task_id: str, **kwargs) -> str:
    """
    Convenience function for publishing task-related events.
    
    Args:
        event_data: Task event data
        task_id: Task ID for correlation
        **kwargs: Additional arguments passed to publish_event
        
    Returns:
        Event ID
    """
    return await publish_event(
        event_data=event_data,
        source="orchestrator",
        correlation_id=task_id,
        tags={"task_id": task_id},
        **kwargs
    )


async def publish_agent_event(event_data: Any, agent_name: str, task_id: Optional[str] = None, **kwargs) -> str:
    """
    Convenience function for publishing agent-related events.
    
    Args:
        event_data: Agent event data
        agent_name: Agent name
        task_id: Optional task ID for correlation
        **kwargs: Additional arguments passed to publish_event
        
    Returns:
        Event ID
    """
    tags = {"agent_name": agent_name}
    if task_id:
        tags["task_id"] = task_id
    
    return await publish_event(
        event_data=event_data,
        source=f"agent:{agent_name}",
        correlation_id=task_id,
        tags=tags,
        **kwargs
    )


async def publish_tool_event(event_data: Any, tool_name: str, agent_name: Optional[str] = None, **kwargs) -> str:
    """
    Convenience function for publishing tool-related events.
    
    Args:
        event_data: Tool event data
        tool_name: Tool name
        agent_name: Optional agent name
        **kwargs: Additional arguments passed to publish_event
        
    Returns:
        Event ID
    """
    tags = {"tool_name": tool_name}
    if agent_name:
        tags["agent_name"] = agent_name
    
    return await publish_event(
        event_data=event_data,
        source=f"tool:{tool_name}",
        tags=tags,
        **kwargs
    ) 