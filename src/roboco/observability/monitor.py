"""
Core Observability Monitor

Integrates with the existing event system to provide comprehensive
monitoring and metrics collection for the Roboco framework.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import time

from ..core.event import Event, EventBus, global_events

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels
        }


@dataclass
class MetricSeries:
    """A time series of metric points."""
    name: str
    description: str
    unit: str
    points: deque = field(default_factory=lambda: deque(maxlen=1000))
    
    def add_point(self, value: float, labels: Optional[Dict[str, str]] = None):
        """Add a metric point."""
        point = MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        )
        self.points.append(point)
    
    def get_latest(self) -> Optional[MetricPoint]:
        """Get the latest metric point."""
        return self.points[-1] if self.points else None
    
    def get_range(self, start: datetime, end: datetime) -> List[MetricPoint]:
        """Get metric points within a time range."""
        return [
            point for point in self.points
            if start <= point.timestamp <= end
        ]
    
    def get_average(self, duration: timedelta) -> Optional[float]:
        """Get average value over a duration."""
        cutoff = datetime.now() - duration
        recent_points = [p for p in self.points if p.timestamp >= cutoff]
        
        if not recent_points:
            return None
        
        return sum(p.value for p in recent_points) / len(recent_points)


class MetricsCollector:
    """Collects and manages metrics from various sources."""
    
    def __init__(self, max_series: int = 100):
        self.metrics: Dict[str, MetricSeries] = {}
        self.max_series = max_series
        self._lock = threading.Lock()
    
    def create_metric(self, name: str, description: str, unit: str = "") -> MetricSeries:
        """Create a new metric series."""
        with self._lock:
            if len(self.metrics) >= self.max_series:
                # Remove oldest metric if at limit
                oldest_name = min(self.metrics.keys(), 
                                key=lambda k: self.metrics[k].points[0].timestamp if self.metrics[k].points else datetime.min)
                del self.metrics[oldest_name]
            
            metric = MetricSeries(name=name, description=description, unit=unit)
            self.metrics[name] = metric
            return metric
    
    def get_metric(self, name: str) -> Optional[MetricSeries]:
        """Get a metric series by name."""
        return self.metrics.get(name)
    
    def record_value(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        metric = self.metrics.get(name)
        if metric:
            metric.add_point(value, labels)
    
    def increment_counter(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        self.record_value(name, 1.0, labels)
    
    def record_duration(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
        """Record a duration metric."""
        self.record_value(name, duration_ms, labels)
    
    def get_all_metrics(self) -> Dict[str, MetricSeries]:
        """Get all metrics."""
        return self.metrics.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        summary = {}
        
        for name, metric in self.metrics.items():
            latest = metric.get_latest()
            avg_1m = metric.get_average(timedelta(minutes=1))
            avg_5m = metric.get_average(timedelta(minutes=5))
            
            summary[name] = {
                "description": metric.description,
                "unit": metric.unit,
                "latest_value": latest.value if latest else None,
                "latest_timestamp": latest.timestamp.isoformat() if latest else None,
                "avg_1m": avg_1m,
                "avg_5m": avg_5m,
                "total_points": len(metric.points)
            }
        
        return summary


class ObservabilityMonitor:
    """Main observability monitor that coordinates all monitoring activities."""
    
    def __init__(self, 
                 event_bus: Optional[EventBus] = None,
                 metrics_collector: Optional[MetricsCollector] = None):
        self.event_bus = event_bus or global_events
        self.metrics = metrics_collector or MetricsCollector()
        self.is_running = False
        self._handlers: List[Callable] = []
        self._start_time = datetime.now()
        
        # Initialize core metrics
        self._init_core_metrics()
        
        # Set up event handlers
        self._setup_event_handlers()
    
    def _init_core_metrics(self):
        """Initialize core system metrics."""
        # Event metrics
        self.metrics.create_metric("events_total", "Total events processed", "count")
        self.metrics.create_metric("events_per_second", "Events processed per second", "events/sec")
        
        # Agent metrics
        self.metrics.create_metric("agents_active", "Number of active agents", "count")
        self.metrics.create_metric("agent_messages_total", "Total agent messages", "count")
        self.metrics.create_metric("agent_response_time", "Agent response time", "ms")
        
        # Brain metrics
        self.metrics.create_metric("brain_thinking_time", "Brain thinking duration", "ms")
        self.metrics.create_metric("brain_reasoning_steps", "Brain reasoning steps", "count")
        self.metrics.create_metric("brain_errors", "Brain errors", "count")
        
        # Tool metrics
        self.metrics.create_metric("tool_executions_total", "Total tool executions", "count")
        self.metrics.create_metric("tool_execution_time", "Tool execution time", "ms")
        self.metrics.create_metric("tool_success_rate", "Tool success rate", "percentage")
        self.metrics.create_metric("tool_errors", "Tool execution errors", "count")
        
        # Memory metrics
        self.metrics.create_metric("memory_operations_total", "Total memory operations", "count")
        self.metrics.create_metric("memory_items_count", "Number of memory items", "count")
        self.metrics.create_metric("memory_search_time", "Memory search time", "ms")
        
        # Team metrics
        self.metrics.create_metric("team_conversations", "Team conversations", "count")
        self.metrics.create_metric("team_speaker_changes", "Speaker changes in teams", "count")
        self.metrics.create_metric("team_collaboration_time", "Team collaboration duration", "ms")
        
        # Task metrics
        self.metrics.create_metric("tasks_created", "Tasks created", "count")
        self.metrics.create_metric("tasks_completed", "Tasks completed", "count")
        self.metrics.create_metric("tasks_failed", "Tasks failed", "count")
        self.metrics.create_metric("task_execution_time", "Task execution time", "ms")
    
    def _setup_event_handlers(self):
        """Set up event handlers for monitoring."""
        
        # Generic event counter
        @self.event_bus.on("*")
        async def count_all_events(event: Event):
            self.metrics.increment_counter("events_total", {"type": event.event_type})
        
        # Brain events
        @self.event_bus.on("brain.thinking.started")
        async def track_brain_thinking_start(event: Event):
            # Store start time for duration calculation
            event.data["_thinking_start"] = time.time()
        
        @self.event_bus.on("brain.thinking.completed")
        async def track_brain_thinking_complete(event: Event):
            start_time = event.data.get("_thinking_start")
            if start_time:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_duration("brain_thinking_time", duration_ms, 
                                           {"agent": event.source})
        
        @self.event_bus.on("brain.reasoning.trace")
        async def track_brain_reasoning(event: Event):
            self.metrics.increment_counter("brain_reasoning_steps", {"agent": event.source})
        
        @self.event_bus.on("brain.error.occurred")
        async def track_brain_errors(event: Event):
            self.metrics.increment_counter("brain_errors", {
                "agent": event.source,
                "error_type": event.data.get("error_type", "unknown")
            })
        
        # Agent events
        @self.event_bus.on("agent.message.sent")
        async def track_agent_messages(event: Event):
            self.metrics.increment_counter("agent_messages_total", {"agent": event.source})
        
        # Tool events
        @self.event_bus.on("tool.started")
        async def track_tool_start(event: Event):
            event.data["_tool_start"] = time.time()
        
        @self.event_bus.on("tool.completed")
        async def track_tool_completion(event: Event):
            start_time = event.data.get("_tool_start")
            if start_time:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_duration("tool_execution_time", duration_ms, {
                    "tool": event.data.get("tool_name", "unknown"),
                    "agent": event.source
                })
            
            self.metrics.increment_counter("tool_executions_total", {
                "tool": event.data.get("tool_name", "unknown"),
                "status": "success"
            })
        
        @self.event_bus.on("tool.failed")
        async def track_tool_failures(event: Event):
            self.metrics.increment_counter("tool_errors", {
                "tool": event.data.get("tool_name", "unknown"),
                "agent": event.source
            })
            
            self.metrics.increment_counter("tool_executions_total", {
                "tool": event.data.get("tool_name", "unknown"),
                "status": "failed"
            })
        
        # Memory events
        @self.event_bus.on("memory.saved")
        async def track_memory_operations(event: Event):
            self.metrics.increment_counter("memory_operations_total", {
                "operation": "save",
                "agent": event.source
            })
        
        @self.event_bus.on("memory.searched")
        async def track_memory_searches(event: Event):
            self.metrics.increment_counter("memory_operations_total", {
                "operation": "search",
                "agent": event.source
            })
            
            duration_ms = event.data.get("duration_ms", 0)
            if duration_ms:
                self.metrics.record_duration("memory_search_time", duration_ms, 
                                           {"agent": event.source})
        
        # Team events
        @self.event_bus.on("team.conversation.started")
        async def track_team_conversations(event: Event):
            self.metrics.increment_counter("team_conversations", {"team": event.source})
            event.data["_conversation_start"] = time.time()
        
        @self.event_bus.on("team.conversation.completed")
        async def track_team_completion(event: Event):
            start_time = event.data.get("_conversation_start")
            if start_time:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_duration("team_collaboration_time", duration_ms, 
                                           {"team": event.source})
        
        @self.event_bus.on("team.speaker.selected")
        async def track_speaker_changes(event: Event):
            self.metrics.increment_counter("team_speaker_changes", {"team": event.source})
        
        # Task events
        @self.event_bus.on("task.created")
        async def track_task_creation(event: Event):
            self.metrics.increment_counter("tasks_created")
            event.data["_task_start"] = time.time()
        
        @self.event_bus.on("task.completed")
        async def track_task_completion(event: Event):
            self.metrics.increment_counter("tasks_completed")
            
            start_time = event.data.get("_task_start")
            if start_time:
                duration_ms = (time.time() - start_time) * 1000
                self.metrics.record_duration("task_execution_time", duration_ms)
        
        @self.event_bus.on("task.failed")
        async def track_task_failures(event: Event):
            self.metrics.increment_counter("tasks_failed")
    
    async def start(self):
        """Start the observability monitor."""
        if self.is_running:
            return
        
        self.is_running = True
        self._start_time = datetime.now()
        
        logger.info("Observability monitor started")
        
        # Start background tasks
        asyncio.create_task(self._update_derived_metrics())
    
    async def stop(self):
        """Stop the observability monitor."""
        self.is_running = False
        logger.info("Observability monitor stopped")
    
    async def _update_derived_metrics(self):
        """Update derived metrics periodically."""
        last_event_count = 0
        
        while self.is_running:
            try:
                # Calculate events per second
                current_events = self.metrics.get_metric("events_total")
                if current_events and current_events.points:
                    total_events = sum(p.value for p in current_events.points)
                    events_this_period = total_events - last_event_count
                    self.metrics.record_value("events_per_second", events_this_period)
                    last_event_count = total_events
                
                # Calculate tool success rate
                tool_executions = self.metrics.get_metric("tool_executions_total")
                tool_errors = self.metrics.get_metric("tool_errors")
                
                if tool_executions and tool_errors:
                    total_executions = sum(p.value for p in tool_executions.points)
                    total_errors = sum(p.value for p in tool_errors.points)
                    
                    if total_executions > 0:
                        success_rate = ((total_executions - total_errors) / total_executions) * 100
                        self.metrics.record_value("tool_success_rate", success_rate)
                
                await asyncio.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error updating derived metrics: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        uptime = datetime.now() - self._start_time
        
        # Get recent error rates
        brain_errors = self.metrics.get_metric("brain_errors")
        tool_errors = self.metrics.get_metric("tool_errors")
        
        recent_brain_errors = 0
        recent_tool_errors = 0
        
        if brain_errors:
            cutoff = datetime.now() - timedelta(minutes=5)
            recent_brain_errors = len([p for p in brain_errors.points if p.timestamp >= cutoff])
        
        if tool_errors:
            cutoff = datetime.now() - timedelta(minutes=5)
            recent_tool_errors = len([p for p in tool_errors.points if p.timestamp >= cutoff])
        
        # Determine health status
        status = "healthy"
        if recent_brain_errors > 10 or recent_tool_errors > 20:
            status = "degraded"
        elif recent_brain_errors > 20 or recent_tool_errors > 50:
            status = "unhealthy"
        
        return {
            "status": status,
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime),
            "recent_brain_errors": recent_brain_errors,
            "recent_tool_errors": recent_tool_errors,
            "total_events": len(self.event_bus.event_history) if hasattr(self.event_bus, 'event_history') else 0,
            "metrics_count": len(self.metrics.metrics),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        summary = {}
        
        # Response times
        brain_thinking = self.metrics.get_metric("brain_thinking_time")
        tool_execution = self.metrics.get_metric("tool_execution_time")
        memory_search = self.metrics.get_metric("memory_search_time")
        
        if brain_thinking:
            summary["avg_brain_thinking_time_ms"] = brain_thinking.get_average(timedelta(minutes=5))
        
        if tool_execution:
            summary["avg_tool_execution_time_ms"] = tool_execution.get_average(timedelta(minutes=5))
        
        if memory_search:
            summary["avg_memory_search_time_ms"] = memory_search.get_average(timedelta(minutes=5))
        
        # Throughput
        events_per_sec = self.metrics.get_metric("events_per_second")
        if events_per_sec:
            summary["events_per_second"] = events_per_sec.get_average(timedelta(minutes=1))
        
        # Success rates
        tool_success = self.metrics.get_metric("tool_success_rate")
        if tool_success:
            summary["tool_success_rate_percent"] = tool_success.get_average(timedelta(minutes=5))
        
        return summary 