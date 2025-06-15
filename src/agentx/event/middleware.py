"""
Event middleware for the AgentX event system.

Provides middleware components for logging, metrics, and custom event processing.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging
import time
from datetime import datetime

from .types import Event

logger = logging.getLogger(__name__)


class EventMiddleware(ABC):
    """Base class for event middleware."""
    
    @abstractmethod
    async def before_publish(self, event: Event) -> None:
        """Called before an event is published."""
        pass
    
    @abstractmethod
    async def before_process(self, event: Event) -> None:
        """Called before an event is processed."""
        pass
    
    @abstractmethod
    async def after_process(self, event: Event) -> None:
        """Called after an event is processed."""
        pass
    
    @abstractmethod
    async def on_error(self, event: Event, error: Exception) -> None:
        """Called when an error occurs during event processing."""
        pass


class LoggingMiddleware(EventMiddleware):
    """Middleware for logging events."""
    
    def __init__(self, log_level: int = logging.INFO):
        self.log_level = log_level
        self.logger = logging.getLogger(f"{__name__}.LoggingMiddleware")
    
    async def before_publish(self, event: Event) -> None:
        """Log event publication."""
        self.logger.log(
            self.log_level,
            f"Publishing event {event.event_id} of type {event.event_type}"
        )
    
    async def before_process(self, event: Event) -> None:
        """Log event processing start."""
        self.logger.log(
            self.log_level,
            f"Processing event {event.event_id} of type {event.event_type}"
        )
    
    async def after_process(self, event: Event) -> None:
        """Log event processing completion."""
        self.logger.log(
            self.log_level,
            f"Completed processing event {event.event_id}"
        )
    
    async def on_error(self, event: Event, error: Exception) -> None:
        """Log event processing error."""
        self.logger.error(
            f"Error processing event {event.event_id}: {error}",
            exc_info=True
        )


class MetricsMiddleware(EventMiddleware):
    """Middleware for collecting event metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'processing_times': [],
            'event_types': {},
            'errors': []
        }
        self._processing_start_times: Dict[str, float] = {}
    
    async def before_publish(self, event: Event) -> None:
        """Record event publication metrics."""
        self.metrics['events_published'] += 1
        
        # Track event types
        event_type = event.event_type
        if event_type not in self.metrics['event_types']:
            self.metrics['event_types'][event_type] = 0
        self.metrics['event_types'][event_type] += 1
    
    async def before_process(self, event: Event) -> None:
        """Record processing start time."""
        self._processing_start_times[event.event_id] = time.time()
    
    async def after_process(self, event: Event) -> None:
        """Record processing completion metrics."""
        self.metrics['events_processed'] += 1
        
        # Calculate processing time
        start_time = self._processing_start_times.pop(event.event_id, None)
        if start_time:
            processing_time = (time.time() - start_time) * 1000  # ms
            self.metrics['processing_times'].append(processing_time)
            
            # Keep only last 1000 processing times
            if len(self.metrics['processing_times']) > 1000:
                self.metrics['processing_times'] = self.metrics['processing_times'][-1000:]
    
    async def on_error(self, event: Event, error: Exception) -> None:
        """Record error metrics."""
        self.metrics['events_failed'] += 1
        
        # Clean up processing time tracking
        self._processing_start_times.pop(event.event_id, None)
        
        # Record error details
        error_info = {
            'event_id': event.event_id,
            'event_type': event.event_type,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now().isoformat()
        }
        self.metrics['errors'].append(error_info)
        
        # Keep only last 100 errors
        if len(self.metrics['errors']) > 100:
            self.metrics['errors'] = self.metrics['errors'][-100:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = self.metrics.copy()
        
        # Calculate average processing time
        if self.metrics['processing_times']:
            metrics['avg_processing_time_ms'] = sum(self.metrics['processing_times']) / len(self.metrics['processing_times'])
        else:
            metrics['avg_processing_time_ms'] = 0.0
        
        return metrics
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self.metrics = {
            'events_published': 0,
            'events_processed': 0,
            'events_failed': 0,
            'processing_times': [],
            'event_types': {},
            'errors': []
        }
        self._processing_start_times.clear()


class FilterMiddleware(EventMiddleware):
    """Middleware for filtering events based on custom criteria."""
    
    def __init__(self, filter_func: callable):
        self.filter_func = filter_func
    
    async def before_publish(self, event: Event) -> None:
        """Apply filter before publishing."""
        if not self.filter_func(event):
            raise ValueError(f"Event {event.event_id} filtered out before publishing")
    
    async def before_process(self, event: Event) -> None:
        """Apply filter before processing."""
        if not self.filter_func(event):
            raise ValueError(f"Event {event.event_id} filtered out before processing")
    
    async def after_process(self, event: Event) -> None:
        """No action needed after processing."""
        pass
    
    async def on_error(self, event: Event, error: Exception) -> None:
        """No action needed on error."""
        pass


class CorrelationMiddleware(EventMiddleware):
    """Middleware for handling event correlation and tracing."""
    
    def __init__(self):
        self.correlation_map: Dict[str, list] = {}
    
    async def before_publish(self, event: Event) -> None:
        """Track correlation before publishing."""
        correlation_id = event.metadata.correlation_id
        if correlation_id:
            if correlation_id not in self.correlation_map:
                self.correlation_map[correlation_id] = []
            self.correlation_map[correlation_id].append({
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'stage': 'published'
            })
    
    async def before_process(self, event: Event) -> None:
        """Track correlation before processing."""
        correlation_id = event.metadata.correlation_id
        if correlation_id and correlation_id in self.correlation_map:
            self.correlation_map[correlation_id].append({
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': datetime.now().isoformat(),
                'stage': 'processing_started'
            })
    
    async def after_process(self, event: Event) -> None:
        """Track correlation after processing."""
        correlation_id = event.metadata.correlation_id
        if correlation_id and correlation_id in self.correlation_map:
            self.correlation_map[correlation_id].append({
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': datetime.now().isoformat(),
                'stage': 'processing_completed'
            })
    
    async def on_error(self, event: Event, error: Exception) -> None:
        """Track correlation on error."""
        correlation_id = event.metadata.correlation_id
        if correlation_id and correlation_id in self.correlation_map:
            self.correlation_map[correlation_id].append({
                'event_id': event.event_id,
                'event_type': event.event_type,
                'timestamp': datetime.now().isoformat(),
                'stage': 'processing_failed',
                'error': str(error)
            })
    
    def get_correlation_trace(self, correlation_id: str) -> Optional[list]:
        """Get the trace for a correlation ID."""
        return self.correlation_map.get(correlation_id)
    
    def cleanup_old_correlations(self, max_age_hours: int = 24) -> None:
        """Clean up old correlation traces."""
        # This is a simplified cleanup - in production you'd want to track timestamps
        # and remove correlations older than max_age_hours
        if len(self.correlation_map) > 10000:  # Simple size-based cleanup
            # Keep only the most recent 5000 correlations
            keys_to_remove = list(self.correlation_map.keys())[:-5000]
            for key in keys_to_remove:
                del self.correlation_map[key] 