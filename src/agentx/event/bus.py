"""
Event Bus implementation for AgentX framework.

Provides a centralized event system with publish/subscribe patterns,
middleware support, and comprehensive observability features.
"""

import asyncio
import logging
import time
import fnmatch
from typing import Any, Dict, List, Optional, Set, Type, Union
from datetime import datetime
from collections import defaultdict
from contextlib import asynccontextmanager

from .types import (
    Event, EventHandler, EventFilter, EventSubscription, EventBusStats,
    EventPriority, EventMetadata
)
from .middleware import EventMiddleware
from ..utils.id import generate_short_id

logger = logging.getLogger(__name__)


class EventBus:
    """
    Centralized event bus for publish/subscribe messaging.
    
    Features:
    - Async/sync event publishing
    - Priority-based event processing
    - Event filtering and routing
    - Middleware support
    - Comprehensive statistics
    - Error handling and retries
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self._subscriptions: Dict[str, List[EventSubscription]] = defaultdict(list)
        self._middleware: List[EventMiddleware] = []
        self._stats = EventBusStats()
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        logger.info(f"EventBus '{name}' initialized")
    
    async def start(self) -> None:
        """Start the event bus worker."""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info(f"EventBus '{self.name}' started")
    
    async def stop(self) -> None:
        """Stop the event bus worker."""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"EventBus '{self.name}' stopped")
    
    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add middleware to the event bus."""
        self._middleware.append(middleware)
        logger.debug(f"Added middleware: {middleware.__class__.__name__}")
    
    def subscribe(
        self,
        event_types: Union[str, List[str]],
        handler: EventHandler,
        filter_func: Optional[EventFilter] = None,
        priority: EventPriority = EventPriority.NORMAL,
        subscription_id: Optional[str] = None
    ) -> str:
        """
        Subscribe to events.
        
        Args:
            event_types: Event type(s) to subscribe to. Supports wildcards:
                        - "*" matches any characters
                        - "?" matches single character
                        - "Agent*" matches "AgentStartEvent", "AgentCompleteEvent", etc.
                        - "*Event" matches all events ending with "Event"
            handler: Event handler function
            filter_func: Optional filter function
            priority: Subscription priority
            subscription_id: Optional custom subscription ID
            
        Returns:
            Subscription ID
        """
        if isinstance(event_types, str):
            event_types = [event_types]
        
        sub_id = subscription_id or generate_short_id()
        
        subscription = EventSubscription(
            subscription_id=sub_id,
            event_types=event_types,
            handler=handler,
            filter_func=filter_func,
            priority=priority
        )
        
        for event_type in event_types:
            self._subscriptions[event_type].append(subscription)
            # Sort by priority (higher priority first)
            self._subscriptions[event_type].sort(
                key=lambda s: s.priority.value, reverse=True
            )
        
        self._stats.active_subscriptions += 1
        logger.debug(f"Subscribed {sub_id} to {event_types}")
        
        return sub_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID to remove
            
        Returns:
            True if subscription was found and removed
        """
        removed = False
        
        for event_type, subscriptions in self._subscriptions.items():
            original_count = len(subscriptions)
            self._subscriptions[event_type] = [
                sub for sub in subscriptions 
                if sub.subscription_id != subscription_id
            ]
            if len(self._subscriptions[event_type]) < original_count:
                removed = True
        
        if removed:
            self._stats.active_subscriptions -= 1
            logger.debug(f"Unsubscribed {subscription_id}")
        
        return removed
    
    async def publish(
        self,
        event_data: Any,
        event_type: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Publish an event.
        
        Args:
            event_data: Event data (should be a Pydantic model)
            event_type: Optional event type override
            priority: Event priority
            source: Event source identifier
            correlation_id: Correlation ID for tracing
            tags: Additional tags
            
        Returns:
            Event ID
        """
        # Determine event type
        if event_type is None:
            if hasattr(event_data, 'type'):
                event_type = event_data.type
            else:
                event_type = event_data.__class__.__name__
        
        # Create event metadata
        metadata = EventMetadata(
            event_id=generate_short_id(),
            priority=priority,
            source=source,
            correlation_id=correlation_id,
            tags=tags or {}
        )
        
        # Create event wrapper
        event = Event(data=event_data, metadata=metadata)
        
        # Apply middleware (pre-publish)
        for middleware in self._middleware:
            try:
                await middleware.before_publish(event)
            except Exception as e:
                logger.error(f"Middleware error in before_publish: {e}")
        
        # Queue event for processing
        await self._event_queue.put(event)
        
        # Update stats
        self._stats.total_events_published += 1
        self._stats.event_types_count[event_type] = (
            self._stats.event_types_count.get(event_type, 0) + 1
        )
        self._stats.last_event_timestamp = datetime.now()
        
        logger.debug(f"Published event {event.event_id} of type {event_type}")
        
        return event.event_id
    
    def publish_sync(
        self,
        event_data: Any,
        event_type: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Synchronous wrapper for publish.
        
        Note: This creates a task but doesn't wait for it in sync context.
        Use publish() in async contexts for proper awaiting.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async context, create task but return immediately
                task = asyncio.create_task(self.publish(
                    event_data, event_type, priority, source, correlation_id, tags
                ))
                return "pending"  # Return placeholder
            else:
                # In sync context, run until complete
                return loop.run_until_complete(self.publish(
                    event_data, event_type, priority, source, correlation_id, tags
                ))
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise
    
    async def _process_events(self) -> None:
        """Process events from the queue."""
        logger.info(f"Event processor started for bus '{self.name}'")
        
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(), timeout=1.0
                )
                
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                # Normal timeout, continue processing
                continue
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                await asyncio.sleep(0.1)  # Brief pause on error
    
    async def _handle_event(self, event: Event) -> None:
        """Handle a single event."""
        start_time = time.time()
        
        try:
            # Apply middleware (pre-process)
            for middleware in self._middleware:
                try:
                    await middleware.before_process(event)
                except Exception as e:
                    logger.error(f"Middleware error in before_process: {e}")
            
            # Get subscribers for this event type (including wildcard matches)
            subscribers = []
            
            # Add exact matches
            subscribers.extend(self._subscriptions.get(event.event_type, []))
            
            # Add wildcard matches
            for pattern, pattern_subscribers in self._subscriptions.items():
                if '*' in pattern or '?' in pattern:
                    if fnmatch.fnmatch(event.event_type, pattern):
                        subscribers.extend(pattern_subscribers)
            
            if not subscribers:
                logger.debug(f"No subscribers for event type: {event.event_type}")
                return
            
            # Process subscribers
            for subscription in subscribers:
                if not subscription.active:
                    continue
                
                try:
                    # Apply filter if present
                    if subscription.filter_func:
                        if not subscription.filter_func(event.data):
                            continue
                    
                    # Call handler
                    if asyncio.iscoroutinefunction(subscription.handler):
                        await subscription.handler(event.data)
                    else:
                        subscription.handler(event.data)
                    
                    logger.debug(f"Event {event.event_id} processed by {subscription.subscription_id}")
                    
                except Exception as e:
                    logger.error(f"Error in event handler {subscription.subscription_id}: {e}")
                    self._stats.total_events_failed += 1
                    
                    # Apply middleware (on error)
                    for middleware in self._middleware:
                        try:
                            await middleware.on_error(event, e)
                        except Exception as me:
                            logger.error(f"Middleware error in on_error: {me}")
            
            # Apply middleware (post-process)
            for middleware in self._middleware:
                try:
                    await middleware.after_process(event)
                except Exception as e:
                    logger.error(f"Middleware error in after_process: {e}")
            
            # Update stats
            self._stats.total_events_processed += 1
            processing_time = (time.time() - start_time) * 1000
            
            # Update average processing time
            total_processed = self._stats.total_events_processed
            current_avg = self._stats.average_processing_time_ms
            self._stats.average_processing_time_ms = (
                (current_avg * (total_processed - 1) + processing_time) / total_processed
            )
            
        except Exception as e:
            logger.error(f"Critical error handling event {event.event_id}: {e}")
            self._stats.total_events_failed += 1
    
    def get_stats(self) -> EventBusStats:
        """Get event bus statistics."""
        return self._stats.model_copy()
    
    def get_subscriptions(self) -> Dict[str, List[str]]:
        """Get current subscriptions by event type."""
        result = {}
        for event_type, subscriptions in self._subscriptions.items():
            result[event_type] = [sub.subscription_id for sub in subscriptions if sub.active]
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        return {
            "name": self.name,
            "running": self._running,
            "queue_size": self._event_queue.qsize(),
            "active_subscriptions": self._stats.active_subscriptions,
            "total_events_published": self._stats.total_events_published,
            "total_events_processed": self._stats.total_events_processed,
            "total_events_failed": self._stats.total_events_failed,
            "average_processing_time_ms": self._stats.average_processing_time_ms
        }


# Global event bus instance
_global_event_bus: Optional[EventBus] = None


def get_event_bus(name: str = "default") -> EventBus:
    """Get or create the global event bus instance."""
    global _global_event_bus
    
    if _global_event_bus is None:
        _global_event_bus = EventBus(name)
    
    return _global_event_bus


async def initialize_event_bus(name: str = "default") -> EventBus:
    """Initialize and start the global event bus."""
    bus = get_event_bus(name)
    await bus.start()
    return bus 