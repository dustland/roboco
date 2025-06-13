"""
Event monitoring and analytics for multi-agent collaboration.

Provides real-time observability, performance tracking, and collaboration analytics
for production Roboco deployments.
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime
import asyncio

from .events import Event
from .bus import EventBus


class TaskMetrics:
    """Container for collaboration performance metrics."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.total_events = 0
        self.event_types: Dict[str, int] = {}
        self.timeline: List[Dict[str, Any]] = []
        
    @property
    def duration_seconds(self) -> float:
        """Get the total monitoring duration in seconds."""
        return (datetime.utcnow() - self.start_time).total_seconds()
    
    @property
    def events_per_second(self) -> float:
        """Get the average events per second."""
        duration = self.duration_seconds
        return self.total_events / duration if duration > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            'monitoring_duration_seconds': self.duration_seconds,
            'total_events': self.total_events,
            'events_per_second': self.events_per_second,
            'event_types': self.event_types,
            'timeline_length': len(self.timeline)
        }


class EventMonitor:
    """
    Real-time event monitoring and analytics for multi-agent collaboration.
    
    Provides comprehensive observability including:
    - Event activity tracking
    - Performance metrics
    - Event timeline
    - Custom event handling
    
    Example:
        monitor = EventMonitor()
        await monitor.start(event_bus)
        
        # Monitor will automatically track events
        # Get real-time stats
        monitor.print_stats()
        
        # Get detailed metrics
        metrics = monitor.get_metrics()
        
        await monitor.stop()
    """
    
    def __init__(self, 
                 print_interval: Optional[float] = None,
                 max_timeline_events: int = 1000):
        """
        Initialize the event monitor.
        
        Args:
            print_interval: If set, automatically print stats every N seconds
            max_timeline_events: Maximum timeline events to keep in memory
        """
        self.metrics = TaskMetrics()
        self.print_interval = print_interval
        self.max_timeline_events = max_timeline_events
        self._monitoring_task: Optional[asyncio.Task] = None
        self._event_bus: Optional[EventBus] = None
        self._custom_handlers: List[Callable[[Event], Awaitable[None]]] = []
        
    async def start(self, event_bus: EventBus) -> None:
        """
        Start monitoring events from the given event bus.
        
        Args:
            event_bus: The event bus to monitor
        """
        self._event_bus = event_bus
        
        # Subscribe to all events
        event_bus.subscribe(Event, self._handle_event)
        
        # Start periodic printing if configured
        if self.print_interval:
            self._monitoring_task = asyncio.create_task(self._periodic_print())
            
    async def stop(self) -> None:
        """Stop monitoring and clean up resources."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
            
        # Unsubscribe from event bus
        if self._event_bus:
            self._event_bus.unsubscribe(Event, self._handle_event)
            self._event_bus = None
    
    def add_custom_handler(self, handler: Callable[[Event], Awaitable[None]]) -> None:
        """
        Add a custom event handler for specialized monitoring.
        
        Args:
            handler: Async function that receives Event objects
        """
        self._custom_handlers.append(handler)
    
    async def _handle_event(self, event: Event) -> None:
        """Handle all events."""
        self.metrics.total_events += 1
        
        # Track event types
        event_type = event.event_type
        if event_type not in self.metrics.event_types:
            self.metrics.event_types[event_type] = 0
        self.metrics.event_types[event_type] += 1
        
        # Add to timeline
        self._add_timeline_event({
            'timestamp': event.timestamp,
            'event_type': event.event_type,
            'source': event.source,
            'event_id': event.event_id,
            'data': event.data
        })
        
        # Call custom handlers
        await self._call_custom_handlers(event)
    
    async def _call_custom_handlers(self, event: Event) -> None:
        """Call all registered custom handlers."""
        for handler in self._custom_handlers:
            try:
                await handler(event)
            except Exception as e:
                # Don't let custom handler errors break monitoring
                print(f"Warning: Custom event handler error: {e}")
    
    def _add_timeline_event(self, timeline_event: Dict[str, Any]) -> None:
        """Add an event to the timeline, maintaining size limit."""
        self.metrics.timeline.append(timeline_event)
        
        # Keep timeline size under control
        if len(self.metrics.timeline) > self.max_timeline_events:
            # Remove oldest events
            self.metrics.timeline = self.metrics.timeline[-self.max_timeline_events:]
    
    async def _periodic_print(self) -> None:
        """Periodically print statistics."""
        while True:
            await asyncio.sleep(self.print_interval)
            self.print_stats()
    
    def print_stats(self) -> None:
        """Print current monitoring statistics."""
        print(f"\n📊 Event Monitoring Stats:")
        print(f"   • Total events: {self.metrics.total_events}")
        print(f"   • Duration: {self.metrics.duration_seconds:.1f}s")
        print(f"   • Events/sec: {self.metrics.events_per_second:.2f}")
        
        if self.metrics.event_types:
            print(f"   • Event types:")
            for event_type, count in sorted(self.metrics.event_types.items()):
                print(f"     - {event_type}: {count}")
    
    def get_metrics(self) -> TaskMetrics:
        """Get the current metrics object."""
        return self.metrics
    
    def get_timeline_events(self, event_type: Optional[str] = None, 
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get timeline events, optionally filtered by type.
        
        Args:
            event_type: Filter by event type (e.g., 'task.started', 'task.completed')
            limit: Maximum number of events to return (most recent first)
            
        Returns:
            List of timeline events
        """
        events = self.metrics.timeline
        
        if event_type:
            events = [e for e in events if e.get('event_type') == event_type]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def reset_metrics(self) -> None:
        """Reset all metrics and start fresh."""
        self.metrics = TaskMetrics() 