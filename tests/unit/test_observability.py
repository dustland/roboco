"""
Tests for the Observability system.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from roboco.observability.monitor import ObservabilityMonitor, MetricsCollector, MetricPoint, MetricSeries
from roboco.core.event import global_events, Event, EventType


class TestMetricPoint:
    """Test MetricPoint class."""
    
    def test_metric_point_creation(self):
        """Test MetricPoint creation."""
        timestamp = datetime.now()
        labels = {"agent": "test_agent", "tool": "web_search"}
        
        point = MetricPoint(
            timestamp=timestamp,
            value=42.5,
            labels=labels
        )
        
        assert point.timestamp == timestamp
        assert point.value == 42.5
        assert point.labels == labels
    
    def test_metric_point_to_dict(self):
        """Test MetricPoint to_dict conversion."""
        timestamp = datetime.now()
        point = MetricPoint(
            timestamp=timestamp,
            value=100.0,
            labels={"type": "test"}
        )
        
        result = point.to_dict()
        
        assert result["timestamp"] == timestamp.isoformat()
        assert result["value"] == 100.0
        assert result["labels"] == {"type": "test"}


class TestMetricSeries:
    """Test MetricSeries class."""
    
    def test_metric_series_creation(self):
        """Test MetricSeries creation."""
        series = MetricSeries(
            name="test_metric",
            description="Test metric description",
            unit="ms"
        )
        
        assert series.name == "test_metric"
        assert series.description == "Test metric description"
        assert series.unit == "ms"
        assert len(series.points) == 0
    
    def test_add_point(self):
        """Test adding points to metric series."""
        series = MetricSeries("test", "Test metric", "count")
        
        series.add_point(10.0, {"label": "value"})
        series.add_point(20.0)
        
        assert len(series.points) == 2
        assert series.points[0].value == 10.0
        assert series.points[0].labels == {"label": "value"}
        assert series.points[1].value == 20.0
        assert series.points[1].labels == {}
    
    def test_get_latest(self):
        """Test getting latest point."""
        series = MetricSeries("test", "Test metric", "count")
        
        # No points
        assert series.get_latest() is None
        
        # Add points
        series.add_point(10.0)
        series.add_point(20.0)
        
        latest = series.get_latest()
        assert latest.value == 20.0
    
    def test_get_range(self):
        """Test getting points in time range."""
        series = MetricSeries("test", "Test metric", "count")
        
        now = datetime.now()
        start = now - timedelta(minutes=10)
        end = now + timedelta(minutes=10)
        
        # Add points with specific timestamps
        old_point = MetricPoint(now - timedelta(minutes=15), 10.0)
        in_range_point = MetricPoint(now, 20.0)
        future_point = MetricPoint(now + timedelta(minutes=15), 30.0)
        
        series.points.extend([old_point, in_range_point, future_point])
        
        range_points = series.get_range(start, end)
        assert len(range_points) == 1
        assert range_points[0].value == 20.0
    
    def test_get_average(self):
        """Test getting average value over duration."""
        series = MetricSeries("test", "Test metric", "count")
        
        now = datetime.now()
        
        # Add points with different timestamps
        old_point = MetricPoint(now - timedelta(minutes=10), 10.0)
        recent_point1 = MetricPoint(now - timedelta(minutes=2), 20.0)
        recent_point2 = MetricPoint(now - timedelta(minutes=1), 30.0)
        
        series.points.extend([old_point, recent_point1, recent_point2])
        
        # Get average for last 5 minutes
        avg = series.get_average(timedelta(minutes=5))
        assert avg == 25.0  # (20 + 30) / 2
        
        # No recent points
        avg_empty = series.get_average(timedelta(seconds=30))
        assert avg_empty is None


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    def test_metrics_collector_creation(self):
        """Test MetricsCollector creation."""
        collector = MetricsCollector(max_series=50)
        
        assert collector.max_series == 50
        assert len(collector.metrics) == 0
    
    def test_create_metric(self):
        """Test creating metrics."""
        collector = MetricsCollector()
        
        series = collector.create_metric("test_metric", "Test description", "ms")
        
        assert series.name == "test_metric"
        assert series.description == "Test description"
        assert series.unit == "ms"
        assert "test_metric" in collector.metrics
    
    def test_get_metric(self):
        """Test getting metrics."""
        collector = MetricsCollector()
        
        # Non-existent metric
        assert collector.get_metric("nonexistent") is None
        
        # Create and get metric
        collector.create_metric("test", "Test", "count")
        metric = collector.get_metric("test")
        assert metric is not None
        assert metric.name == "test"
    
    def test_record_value(self):
        """Test recording metric values."""
        collector = MetricsCollector()
        collector.create_metric("test", "Test", "count")
        
        collector.record_value("test", 42.0, {"label": "value"})
        
        metric = collector.get_metric("test")
        assert len(metric.points) == 1
        assert metric.points[0].value == 42.0
        assert metric.points[0].labels == {"label": "value"}
    
    def test_increment_counter(self):
        """Test incrementing counters."""
        collector = MetricsCollector()
        collector.create_metric("counter", "Counter", "count")
        
        collector.increment_counter("counter", {"type": "test"})
        collector.increment_counter("counter", {"type": "test"})
        
        metric = collector.get_metric("counter")
        assert len(metric.points) == 2
        assert all(p.value == 1.0 for p in metric.points)
    
    def test_record_duration(self):
        """Test recording durations."""
        collector = MetricsCollector()
        collector.create_metric("duration", "Duration", "ms")
        
        collector.record_duration("duration", 1500.0, {"operation": "test"})
        
        metric = collector.get_metric("duration")
        assert len(metric.points) == 1
        assert metric.points[0].value == 1500.0
        assert metric.points[0].labels == {"operation": "test"}
    
    def test_get_all_metrics(self):
        """Test getting all metrics."""
        collector = MetricsCollector()
        
        collector.create_metric("metric1", "First", "count")
        collector.create_metric("metric2", "Second", "ms")
        
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) == 2
        assert "metric1" in all_metrics
        assert "metric2" in all_metrics
    
    def test_get_summary(self):
        """Test getting metrics summary."""
        collector = MetricsCollector()
        
        collector.create_metric("test", "Test", "count")
        collector.record_value("test", 10.0)
        collector.record_value("test", 20.0)
        
        summary = collector.get_summary()
        assert "test" in summary
        assert summary["test"]["description"] == "Test"
        assert summary["test"]["unit"] == "count"
        assert summary["test"]["total_points"] == 2
        assert summary["test"]["latest_value"] == 20.0


class TestObservabilityMonitor:
    """Test ObservabilityMonitor class."""
    
    def test_monitor_creation(self):
        """Test ObservabilityMonitor creation."""
        monitor = ObservabilityMonitor()
        
        assert monitor.event_bus is not None
        assert monitor.metrics is not None
        assert not monitor.is_running
        assert len(monitor.metrics.metrics) > 0  # Core metrics should be initialized
    
    def test_monitor_with_custom_components(self):
        """Test monitor with custom event bus and metrics collector."""
        custom_metrics = MetricsCollector(max_series=200)
        
        monitor = ObservabilityMonitor(
            event_bus=global_events,
            metrics_collector=custom_metrics
        )
        
        assert monitor.metrics is custom_metrics
        assert monitor.metrics.max_series == 200
    
    @pytest.mark.asyncio
    async def test_monitor_start_stop(self):
        """Test starting and stopping the monitor."""
        monitor = ObservabilityMonitor()
        
        assert not monitor.is_running
        
        await monitor.start()
        assert monitor.is_running
        
        await monitor.stop()
        assert not monitor.is_running
    
    @pytest.mark.asyncio
    async def test_monitor_start_idempotent(self):
        """Test that starting an already running monitor is safe."""
        monitor = ObservabilityMonitor()
        
        await monitor.start()
        assert monitor.is_running
        
        # Starting again should be safe
        await monitor.start()
        assert monitor.is_running
        
        await monitor.stop()
    
    def test_get_system_health(self):
        """Test getting system health."""
        monitor = ObservabilityMonitor()
        
        health = monitor.get_system_health()
        
        assert "status" in health
        assert "uptime_seconds" in health
        assert "uptime_human" in health
        assert "total_events" in health
        assert "metrics_count" in health
        assert "timestamp" in health
        
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert isinstance(health["uptime_seconds"], float)
        assert isinstance(health["total_events"], int)
        assert isinstance(health["metrics_count"], int)
    
    def test_get_performance_summary(self):
        """Test getting performance summary."""
        monitor = ObservabilityMonitor()
        
        # Add some test data
        monitor.metrics.create_metric("test_metric", "Test", "ms")
        monitor.metrics.record_value("test_metric", 100.0)
        
        summary = monitor.get_performance_summary()
        
        assert isinstance(summary, dict)
        # Summary should contain performance metrics when available


class TestEventIntegration:
    """Test event system integration with observability."""
    
    def test_event_handler_registration(self):
        """Test that event handlers are properly registered."""
        monitor = ObservabilityMonitor()
        
        # Check that event handlers are registered
        assert len(global_events.listeners) > 0
        
        # Check for specific event types
        expected_events = [
            "brain.thinking.started",
            "brain.thinking.completed",
            "tool.started",
            "tool.completed",
            "tool.failed",
            "memory.saved",
            "memory.searched"
        ]
        
        for event_type in expected_events:
            assert event_type in global_events.listeners
            assert len(global_events.listeners[event_type]) > 0
    
    def test_brain_event_tracking(self):
        """Test brain event tracking."""
        monitor = ObservabilityMonitor()
        
        # Emit brain thinking events
        global_events.emit("brain.thinking.started", {
            "model": "deepseek-chat",
            "agent": "test_agent"
        }, source="test_agent")
        
        global_events.emit("brain.thinking.completed", {
            "model": "deepseek-chat",
            "duration_ms": 1500.0,
            "agent": "test_agent",
            "_thinking_start": time.time() - 1.5
        }, source="test_agent")
        
        # Check metrics were recorded
        thinking_time_metric = monitor.metrics.get_metric("brain_thinking_time")
        assert thinking_time_metric is not None
        
        events_metric = monitor.metrics.get_metric("events_total")
        assert events_metric is not None
        assert len(events_metric.points) >= 2
    
    def test_tool_event_tracking(self):
        """Test tool event tracking."""
        monitor = ObservabilityMonitor()
        
        # Emit tool events
        global_events.emit("tool.started", {
            "tool_name": "web_search",
            "agent": "test_agent"
        }, source="test_agent")
        
        global_events.emit("tool.completed", {
            "tool_name": "web_search",
            "duration_ms": 800.0,
            "agent": "test_agent",
            "_tool_start": time.time() - 0.8
        }, source="test_agent")
        
        # Check metrics
        tool_execution_metric = monitor.metrics.get_metric("tool_execution_time")
        assert tool_execution_metric is not None
        
        tool_executions_metric = monitor.metrics.get_metric("tool_executions_total")
        assert tool_executions_metric is not None
    
    def test_tool_failure_tracking(self):
        """Test tool failure tracking."""
        monitor = ObservabilityMonitor()
        
        global_events.emit("tool.failed", {
            "tool_name": "web_search",
            "error": "Connection timeout",
            "agent": "test_agent"
        }, source="test_agent")
        
        # Check error metrics
        tool_errors_metric = monitor.metrics.get_metric("tool_errors")
        assert tool_errors_metric is not None
        assert len(tool_errors_metric.points) >= 1
    
    def test_memory_event_tracking(self):
        """Test memory event tracking."""
        monitor = ObservabilityMonitor()
        
        global_events.emit("memory.saved", {
            "operation": "save",
            "agent": "test_agent",
            "content_size": 1024
        }, source="test_agent")
        
        global_events.emit("memory.searched", {
            "operation": "search",
            "duration_ms": 50.0,
            "agent": "test_agent"
        }, source="test_agent")
        
        # Check metrics
        memory_ops_metric = monitor.metrics.get_metric("memory_operations_total")
        assert memory_ops_metric is not None
        assert len(memory_ops_metric.points) >= 2


class TestObservabilityIntegration:
    """Integration tests for the complete observability system."""
    
    @pytest.mark.asyncio
    async def test_full_system_simulation(self):
        """Test a complete system simulation with multiple events."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            # Simulate brain activity
            for i in range(3):
                agent = f"agent_{i}"
                
                global_events.emit("brain.thinking.started", {
                    "model": "deepseek-chat",
                    "agent": agent
                }, source=agent)
                
                await asyncio.sleep(0.01)  # Small delay
                
                global_events.emit("brain.thinking.completed", {
                    "model": "deepseek-chat",
                    "duration_ms": 1000.0 + i * 100,
                    "agent": agent,
                    "_thinking_start": time.time() - (1.0 + i * 0.1)
                }, source=agent)
            
            # Simulate tool usage
            tools = ["web_search", "read_file", "write_file"]
            for i, tool in enumerate(tools):
                agent = f"agent_{i % 2}"
                
                global_events.emit("tool.started", {
                    "tool_name": tool,
                    "agent": agent
                }, source=agent)
                
                await asyncio.sleep(0.01)
                
                if i < 2:  # Success
                    global_events.emit("tool.completed", {
                        "tool_name": tool,
                        "duration_ms": 500.0 + i * 100,
                        "agent": agent,
                        "_tool_start": time.time() - (0.5 + i * 0.1)
                    }, source=agent)
                else:  # Failure
                    global_events.emit("tool.failed", {
                        "tool_name": tool,
                        "error": "Simulated failure",
                        "agent": agent
                    }, source=agent)
            
            # Simulate memory operations
            for i in range(2):
                agent = f"agent_{i}"
                operation = "saved" if i == 0 else "searched"
                
                global_events.emit(f"memory.{operation}", {
                    "operation": operation,
                    "duration_ms": 100.0 + i * 50,
                    "agent": agent
                }, source=agent)
            
            # Wait for processing
            await asyncio.sleep(0.1)
            
            # Verify system health
            health = monitor.get_system_health()
            assert health["status"] in ["healthy", "degraded", "unhealthy"]
            assert health["total_events"] >= 10  # Should have captured all events
            
            # Verify performance summary
            performance = monitor.get_performance_summary()
            assert isinstance(performance, dict)
            
            # Verify specific metrics
            brain_metric = monitor.metrics.get_metric("brain_thinking_time")
            assert brain_metric is not None
            assert len(brain_metric.points) >= 3
            
            tool_metric = monitor.metrics.get_metric("tool_execution_time")
            assert tool_metric is not None
            assert len(tool_metric.points) >= 2
            
            tool_errors = monitor.metrics.get_metric("tool_errors")
            assert tool_errors is not None
            assert len(tool_errors.points) >= 1
            
            memory_metric = monitor.metrics.get_metric("memory_operations_total")
            assert memory_metric is not None
            assert len(memory_metric.points) >= 2
            
        finally:
            await monitor.stop()
    
    def test_metrics_collection_performance(self):
        """Test that metrics collection doesn't significantly impact performance."""
        monitor = ObservabilityMonitor()
        
        start_time = time.time()
        
        # Emit many events quickly using a registered event type
        for i in range(100):
            global_events.emit("brain.thinking.started", {
                "model": "deepseek-chat",
                "agent": f"performance_test_agent_{i % 10}",
                "iteration": i
            }, source=f"performance_test_agent_{i % 10}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly (less than 1 second for 100 events)
        assert duration < 1.0
        
        # Wait a bit for event processing
        time.sleep(0.1)
        
        # Verify events were captured
        events_metric = monitor.metrics.get_metric("events_total")
        assert events_metric is not None
        # Events should be captured since we're using a registered event type
        assert len(events_metric.points) >= 100
    
    def test_memory_usage_bounds(self):
        """Test that the observability system respects memory bounds."""
        monitor = ObservabilityMonitor()
        
        # Create a metric with limited history
        test_metric = monitor.metrics.create_metric("test_bounded", "Test", "count")
        
        # Add more points than the limit
        for i in range(1500):  # More than default 1000 limit
            monitor.metrics.record_value("test_bounded", float(i))
        
        # Should be limited to maxlen
        assert len(test_metric.points) <= 1000
        
        # Should contain the most recent points
        latest_values = [p.value for p in list(test_metric.points)[-10:]]
        expected_values = list(range(1490, 1500))  # Last 10 values
        assert latest_values == [float(v) for v in expected_values]


if __name__ == "__main__":
    pytest.main([__file__]) 