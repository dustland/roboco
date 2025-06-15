"""
Event subscribers for the AgentX event system.

Provides base classes and utilities for creating event subscribers.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict
import logging
from datetime import datetime

from .types import EventHandler, EventFilter, EventPriority
from .bus import get_event_bus

logger = logging.getLogger(__name__)


class EventSubscriber(ABC):
    """Base class for event subscribers."""
    
    def __init__(self, name: str):
        self.name = name
        self.subscription_ids: List[str] = []
        self.event_bus = get_event_bus()
        self._active = False
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """Return list of event types this subscriber handles."""
        pass
    
    @abstractmethod
    def handle_event(self, event_data: Any) -> None:
        """Handle an event."""
        pass
    
    def get_filter(self) -> Optional[EventFilter]:
        """Return optional filter function for events."""
        return None
    
    def get_priority(self) -> EventPriority:
        """Return subscription priority."""
        return EventPriority.NORMAL
    
    def start(self) -> None:
        """Start subscribing to events."""
        if self._active:
            return
        
        event_types = self.get_event_types()
        filter_func = self.get_filter()
        priority = self.get_priority()
        
        for event_type in event_types:
            subscription_id = self.event_bus.subscribe(
                event_types=[event_type],
                handler=self.handle_event,
                filter_func=filter_func,
                priority=priority,
                subscription_id=f"{self.name}_{event_type}"
            )
            self.subscription_ids.append(subscription_id)
        
        self._active = True
        logger.info(f"Subscriber '{self.name}' started for events: {event_types}")
    
    def stop(self) -> None:
        """Stop subscribing to events."""
        if not self._active:
            return
        
        for subscription_id in self.subscription_ids:
            self.event_bus.unsubscribe(subscription_id)
        
        self.subscription_ids.clear()
        self._active = False
        logger.info(f"Subscriber '{self.name}' stopped")
    
    def is_active(self) -> bool:
        """Check if subscriber is active."""
        return self._active


class AsyncEventSubscriber(ABC):
    """Base class for async event subscribers."""
    
    def __init__(self, name: str):
        self.name = name
        self.subscription_ids: List[str] = []
        self.event_bus = get_event_bus()
        self._active = False
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """Return list of event types this subscriber handles."""
        pass
    
    @abstractmethod
    async def handle_event(self, event_data: Any) -> None:
        """Handle an event asynchronously."""
        pass
    
    def get_filter(self) -> Optional[EventFilter]:
        """Return optional filter function for events."""
        return None
    
    def get_priority(self) -> EventPriority:
        """Return subscription priority."""
        return EventPriority.NORMAL
    
    def start(self) -> None:
        """Start subscribing to events."""
        if self._active:
            return
        
        event_types = self.get_event_types()
        filter_func = self.get_filter()
        priority = self.get_priority()
        
        for event_type in event_types:
            subscription_id = self.event_bus.subscribe(
                event_types=[event_type],
                handler=self.handle_event,
                filter_func=filter_func,
                priority=priority,
                subscription_id=f"{self.name}_{event_type}"
            )
            self.subscription_ids.append(subscription_id)
        
        self._active = True
        logger.info(f"Async subscriber '{self.name}' started for events: {event_types}")
    
    def stop(self) -> None:
        """Stop subscribing to events."""
        if not self._active:
            return
        
        for subscription_id in self.subscription_ids:
            self.event_bus.unsubscribe(subscription_id)
        
        self.subscription_ids.clear()
        self._active = False
        logger.info(f"Async subscriber '{self.name}' stopped")
    
    def is_active(self) -> bool:
        """Check if subscriber is active."""
        return self._active


class ObservabilitySubscriber(AsyncEventSubscriber):
    """Subscriber for observability events."""
    
    def __init__(self, name: str = "observability"):
        super().__init__(name)
        self.events_received: List[Dict[str, Any]] = []
    
    def get_event_types(self) -> List[str]:
        """Subscribe to all event types for observability."""
        return [
            "event_task_start",
            "event_task_complete",
            "event_task_paused",
            "event_task_resumed",
            "event_agent_start",
            "event_agent_complete",
            "event_agent_handoff",
            "event_tool_call",
            "event_tool_result",
            "event_error",
            "event_memory_store",
            "event_memory_retrieve",
        ]
    
    async def handle_event(self, event_data: Any) -> None:
        """Handle observability events."""
        event_info = {
            'timestamp': datetime.now().isoformat(),
            'event_type': getattr(event_data, 'type', event_data.__class__.__name__),
            'data': event_data.model_dump() if hasattr(event_data, 'model_dump') else str(event_data)
        }
        
        self.events_received.append(event_info)
        
        # Keep only last 1000 events
        if len(self.events_received) > 1000:
            self.events_received = self.events_received[-1000:]
        
        logger.debug(f"Observability: Received {event_info['event_type']} event")
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events for observability."""
        return self.events_received[-limit:]
    
    def get_events_by_type(self, event_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events of a specific type."""
        filtered_events = [
            event for event in self.events_received 
            if event['event_type'] == event_type
        ]
        return filtered_events[-limit:]


class MetricsSubscriber(AsyncEventSubscriber):
    """Subscriber for collecting metrics from events."""
    
    def __init__(self, name: str = "metrics"):
        super().__init__(name)
        self.metrics: Dict[str, Any] = {
            'task_count': 0,
            'agent_turns': 0,
            'tool_calls': 0,
            'errors': 0,
            'task_durations': [],
            'agent_performance': {},
        }
    
    def get_event_types(self) -> List[str]:
        """Subscribe to metric-relevant events."""
        return [
            "event_task_start",
            "event_task_complete",
            "event_agent_complete",
            "event_tool_call",
            "event_error",
        ]
    
    async def handle_event(self, event_data: Any) -> None:
        """Handle metric events."""
        event_type = getattr(event_data, 'type', event_data.__class__.__name__)
        
        if event_type == "event_task_start":
            self.metrics['task_count'] += 1
        
        elif event_type == "event_task_complete":
            if hasattr(event_data, 'total_duration_ms'):
                self.metrics['task_durations'].append(event_data.total_duration_ms)
                # Keep only last 100 durations
                if len(self.metrics['task_durations']) > 100:
                    self.metrics['task_durations'] = self.metrics['task_durations'][-100:]
        
        elif event_type == "event_agent_complete":
            self.metrics['agent_turns'] += 1
            
            if hasattr(event_data, 'agent_name'):
                agent_name = event_data.agent_name
                if agent_name not in self.metrics['agent_performance']:
                    self.metrics['agent_performance'][agent_name] = {
                        'turns': 0,
                        'total_time_ms': 0,
                        'avg_time_ms': 0
                    }
                
                self.metrics['agent_performance'][agent_name]['turns'] += 1
                
                if hasattr(event_data, 'execution_time_ms') and event_data.execution_time_ms:
                    total_time = self.metrics['agent_performance'][agent_name]['total_time_ms']
                    total_time += event_data.execution_time_ms
                    self.metrics['agent_performance'][agent_name]['total_time_ms'] = total_time
                    
                    turns = self.metrics['agent_performance'][agent_name]['turns']
                    self.metrics['agent_performance'][agent_name]['avg_time_ms'] = total_time / turns
        
        elif event_type == "event_tool_call":
            self.metrics['tool_calls'] += 1
        
        elif event_type == "event_error":
            self.metrics['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = self.metrics.copy()
        
        # Calculate average task duration
        if self.metrics['task_durations']:
            metrics['avg_task_duration_ms'] = sum(self.metrics['task_durations']) / len(self.metrics['task_durations'])
        else:
            metrics['avg_task_duration_ms'] = 0.0
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            'task_count': 0,
            'agent_turns': 0,
            'tool_calls': 0,
            'errors': 0,
            'task_durations': [],
            'agent_performance': {},
        } 