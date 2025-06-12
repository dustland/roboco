"""
Event monitoring and analytics for multi-agent collaboration.

Provides real-time observability, performance tracking, and collaboration analytics
for production Roboco deployments.
"""

from typing import Dict, List, Any, Optional, Callable, Awaitable
from datetime import datetime
import asyncio

from .events import (
    Event, AgentEvent, ToolEvent, SystemEvent,
    MessageSentEvent, MessageReceivedEvent,
    ToolCallInitiatedEvent, ToolCallCompletedEvent,
    SystemStartedEvent, ErrorOccurredEvent
)
from .bus import EventBus


class CollaborationMetrics:
    """Container for collaboration performance metrics."""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.total_events = 0
        self.agent_stats: Dict[str, Dict[str, Any]] = {}
        self.tool_stats: Dict[str, Dict[str, Any]] = {}
        self.timeline: List[Dict[str, Any]] = []
        self.error_count = 0
        
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
            'error_count': self.error_count,
            'agent_statistics': self.agent_stats,
            'tool_statistics': self.tool_stats,
            'timeline_length': len(self.timeline)
        }


class EventMonitor:
    """
    Real-time event monitoring and analytics for multi-agent collaboration.
    
    Provides comprehensive observability including:
    - Agent activity tracking
    - Tool usage analytics  
    - Performance metrics
    - Collaboration timeline
    - Error monitoring
    
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
        self.metrics = CollaborationMetrics()
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
        
        # Subscribe to different event types
        event_bus.subscribe(AgentEvent, self._handle_agent_event)
        event_bus.subscribe(ToolEvent, self._handle_tool_event)
        event_bus.subscribe(SystemEvent, self._handle_system_event)
        event_bus.subscribe(Event, self._handle_generic_event)
        
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
            self._event_bus.unsubscribe(AgentEvent, self._handle_agent_event)
            self._event_bus.unsubscribe(ToolEvent, self._handle_tool_event)
            self._event_bus.unsubscribe(SystemEvent, self._handle_system_event)
            self._event_bus.unsubscribe(Event, self._handle_generic_event)
            self._event_bus = None
    
    def add_custom_handler(self, handler: Callable[[Event], Awaitable[None]]) -> None:
        """
        Add a custom event handler for specialized monitoring.
        
        Args:
            handler: Async function that receives Event objects
        """
        self._custom_handlers.append(handler)
    
    async def _handle_agent_event(self, event: AgentEvent) -> None:
        """Handle agent-related events."""
        self.metrics.total_events += 1
        
        agent_id = getattr(event, 'agent_id', 'unknown')
        if agent_id not in self.metrics.agent_stats:
            self.metrics.agent_stats[agent_id] = {
                'messages_sent': 0,
                'messages_received': 0,
                'total_events': 0,
                'first_activity': event.timestamp,
                'last_activity': event.timestamp
            }
        
        stats = self.metrics.agent_stats[agent_id]
        stats['total_events'] += 1
        stats['last_activity'] = event.timestamp
        
        if isinstance(event, MessageSentEvent):
            stats['messages_sent'] += 1
            self._add_timeline_event({
                'timestamp': event.timestamp,
                'type': 'message_sent',
                'agent': agent_id,
                'recipient': getattr(event, 'recipient_agent_id', 'broadcast'),
                'message_id': event.message_id
            })
            
        elif isinstance(event, MessageReceivedEvent):
            stats['messages_received'] += 1
            self._add_timeline_event({
                'timestamp': event.timestamp,
                'type': 'message_received',
                'agent': agent_id,
                'sender': getattr(event, 'sender_agent_id', 'system'),
                'message_id': event.message_id
            })
        
        # Call custom handlers
        await self._call_custom_handlers(event)
    
    async def _handle_tool_event(self, event: ToolEvent) -> None:
        """Handle tool-related events."""
        self.metrics.total_events += 1
        
        tool_name = getattr(event, 'tool_name', 'unknown')
        if tool_name not in self.metrics.tool_stats:
            self.metrics.tool_stats[tool_name] = {
                'calls_initiated': 0,
                'calls_completed': 0,
                'calls_failed': 0,
                'total_execution_time': 0.0,
                'average_execution_time': 0.0
            }
        
        stats = self.metrics.tool_stats[tool_name]
        
        if isinstance(event, ToolCallInitiatedEvent):
            stats['calls_initiated'] += 1
            self._add_timeline_event({
                'timestamp': event.timestamp,
                'type': 'tool_call_started',
                'tool': tool_name,
                'agent': getattr(event, 'agent_id', 'unknown'),
                'call_id': getattr(event, 'tool_call_id', 'unknown')
            })
            
        elif isinstance(event, ToolCallCompletedEvent):
            if hasattr(event, 'error') and event.error:
                stats['calls_failed'] += 1
            else:
                stats['calls_completed'] += 1
                
            if hasattr(event, 'execution_time_ms') and event.execution_time_ms:
                stats['total_execution_time'] += event.execution_time_ms
                completed_calls = stats['calls_completed'] + stats['calls_failed']
                if completed_calls > 0:
                    stats['average_execution_time'] = stats['total_execution_time'] / completed_calls
            
            self._add_timeline_event({
                'timestamp': event.timestamp,
                'type': 'tool_call_completed',
                'tool': tool_name,
                'agent': getattr(event, 'agent_id', 'unknown'),
                'success': not (hasattr(event, 'error') and event.error),
                'execution_time': getattr(event, 'execution_time_ms', 0)
            })
        
        # Call custom handlers
        await self._call_custom_handlers(event)
    
    async def _handle_system_event(self, event: SystemEvent) -> None:
        """Handle system-level events."""
        self.metrics.total_events += 1
        
        if isinstance(event, SystemStartedEvent):
            self._add_timeline_event({
                'timestamp': event.timestamp,
                'type': 'system_started',
                'source': event.source
            })
        elif isinstance(event, ErrorOccurredEvent):
            self.metrics.error_count += 1
            self._add_timeline_event({
                'timestamp': event.timestamp,
                'type': 'error',
                'error_type': getattr(event, 'error_type', 'unknown'),
                'message': event.error_message
            })
        
        # Call custom handlers
        await self._call_custom_handlers(event)
    
    async def _handle_generic_event(self, event: Event) -> None:
        """Handle any other events."""
        # Only count events not already handled by specific handlers
        if not isinstance(event, (AgentEvent, ToolEvent, SystemEvent)):
            self.metrics.total_events += 1
        
        # Call custom handlers for all events
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
        print(f"\n📊 Collaboration Monitoring Stats:")
        print(f"   • Total events: {self.metrics.total_events}")
        print(f"   • Duration: {self.metrics.duration_seconds:.1f}s")
        print(f"   • Events/sec: {self.metrics.events_per_second:.2f}")
        print(f"   • Active agents: {len(self.metrics.agent_stats)}")
        print(f"   • Tools used: {len(self.metrics.tool_stats)}")
        
        if self.metrics.error_count > 0:
            print(f"   • Errors: {self.metrics.error_count}")
        
        if self.metrics.agent_stats:
            print(f"   • Agent activity:")
            for agent_id, stats in self.metrics.agent_stats.items():
                print(f"     - {agent_id}: {stats['messages_sent']} sent, {stats['messages_received']} received")
        
        if self.metrics.tool_stats:
            print(f"   • Tool usage:")
            for tool_name, stats in self.metrics.tool_stats.items():
                success_rate = (stats['calls_completed'] / max(1, stats['calls_initiated'])) * 100
                print(f"     - {tool_name}: {stats['calls_completed']}/{stats['calls_initiated']} calls ({success_rate:.1f}% success)")
    
    def get_metrics(self) -> CollaborationMetrics:
        """Get the current metrics object."""
        return self.metrics
    
    def get_agent_activity(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get activity statistics for a specific agent."""
        return self.metrics.agent_stats.get(agent_id)
    
    def get_tool_usage(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get usage statistics for a specific tool."""
        return self.metrics.tool_stats.get(tool_name)
    
    def get_timeline_events(self, event_type: Optional[str] = None, 
                           limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get timeline events, optionally filtered by type.
        
        Args:
            event_type: Filter by event type (e.g., 'message_sent', 'tool_call_started')
            limit: Maximum number of events to return (most recent first)
            
        Returns:
            List of timeline events
        """
        events = self.metrics.timeline
        
        if event_type:
            events = [e for e in events if e.get('type') == event_type]
        
        if limit:
            events = events[-limit:]
        
        return events
    
    def get_error_events(self) -> List[Dict[str, Any]]:
        """Get all error events from the timeline."""
        return self.get_timeline_events('error')
    
    def reset_metrics(self) -> None:
        """Reset all metrics and start fresh."""
        self.metrics = CollaborationMetrics() 