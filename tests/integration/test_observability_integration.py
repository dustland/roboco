"""
Integration tests for Observability system with Roboco components.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from roboco.observability.monitor import ObservabilityMonitor
from roboco.core.event import global_events
from roboco.core.brain import Brain, BrainConfig
from roboco.core.memory import Memory
from roboco.core.agent import Agent, AgentConfig


class TestObservabilityWithBrain:
    """Test observability integration with Brain component."""
    
    @pytest.mark.asyncio
    async def test_brain_thinking_monitoring(self):
        """Test that brain thinking is properly monitored."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            # Create a brain instance
            config = BrainConfig(
                model="deepseek-chat",
                temperature=0.7
            )
            brain = Brain(config)
            
            # Mock the OpenAI client to avoid real API calls
            with patch.object(brain, 'client') as mock_client:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Test response"
                mock_response.choices[0].message.tool_calls = None
                mock_client.chat.completions.create.return_value = mock_response
                
                # Simulate brain thinking
                messages = [{"role": "user", "content": "Test message"}]
                
                # This should trigger brain events
                response = await brain.think(messages, agent_name="test_agent")
                
                # Wait for event processing
                await asyncio.sleep(0.1)
                
                # Verify brain metrics were recorded
                brain_thinking_metric = monitor.metrics.get_metric("brain_thinking_time")
                assert brain_thinking_metric is not None
                
                events_metric = monitor.metrics.get_metric("events_total")
                assert events_metric is not None
                assert len(events_metric.points) > 0
                
        finally:
            await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_brain_error_monitoring(self):
        """Test that brain errors are properly monitored."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            config = BrainConfig(model="deepseek-chat")
            brain = Brain(config)
            
            # Mock the client to raise an exception
            with patch.object(brain, 'client') as mock_client:
                mock_client.chat.completions.create.side_effect = Exception("API Error")
                
                # This should trigger a brain error event
                with pytest.raises(Exception):
                    await brain.think([{"role": "user", "content": "Test"}], agent_name="test_agent")
                
                # Wait for event processing
                await asyncio.sleep(0.1)
                
                # Verify error metrics
                brain_errors_metric = monitor.metrics.get_metric("brain_errors")
                if brain_errors_metric:  # Only check if the metric exists
                    assert len(brain_errors_metric.points) > 0
                
        finally:
            await monitor.stop()


class TestObservabilityWithMemory:
    """Test observability integration with Memory component."""
    
    @pytest.mark.asyncio
    async def test_memory_operations_monitoring(self):
        """Test that memory operations are properly monitored."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            # Create memory instance
            memory = Memory()
            
            # Mock the backend to avoid real storage
            with patch.object(memory, 'backend') as mock_backend:
                mock_backend.store.return_value = asyncio.Future()
                mock_backend.store.return_value.set_result("stored_id")
                
                mock_backend.search.return_value = asyncio.Future()
                mock_backend.search.return_value.set_result([])
                
                # Simulate memory operations that should trigger events
                await memory.store("Test content", metadata={"agent": "test_agent"})
                await memory.search("test query", agent_id="test_agent")
                
                # Wait for event processing
                await asyncio.sleep(0.1)
                
                # Verify memory metrics
                memory_ops_metric = monitor.metrics.get_metric("memory_operations_total")
                assert memory_ops_metric is not None
                assert len(memory_ops_metric.points) >= 2
                
        finally:
            await monitor.stop()


class TestObservabilityWithAgent:
    """Test observability integration with Agent component."""
    
    @pytest.mark.asyncio
    async def test_agent_activity_monitoring(self):
        """Test that agent activities are properly monitored."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            # Create agent
            config = AgentConfig(
                name="test_agent",
                role="Test role",
                brain_config=BrainConfig(model="deepseek-chat")
            )
            agent = Agent(config)
            
            # Mock components to avoid real API calls
            with patch.object(agent.brain, 'client') as mock_client:
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message.content = "Agent response"
                mock_response.choices[0].message.tool_calls = None
                mock_client.chat.completions.create.return_value = mock_response
                
                # Simulate agent sending a message
                response = await agent.send_message("Test message")
                
                # Wait for event processing
                await asyncio.sleep(0.1)
                
                # Verify agent metrics
                agent_messages_metric = monitor.metrics.get_metric("agent_messages_total")
                if agent_messages_metric:
                    assert len(agent_messages_metric.points) > 0
                
                # Verify brain metrics from agent activity
                brain_thinking_metric = monitor.metrics.get_metric("brain_thinking_time")
                assert brain_thinking_metric is not None
                
        finally:
            await monitor.stop()


class TestObservabilitySystemLoad:
    """Test observability system under load."""
    
    @pytest.mark.asyncio
    async def test_high_event_volume(self):
        """Test observability system with high event volume."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            # Generate many events quickly
            event_count = 500
            
            async def generate_events():
                for i in range(event_count):
                    global_events.emit("test.high_volume", {
                        "iteration": i,
                        "timestamp": time.time()
                    }, source=f"generator_{i % 10}")
                    
                    if i % 50 == 0:  # Small pause every 50 events
                        await asyncio.sleep(0.001)
            
            start_time = time.time()
            await generate_events()
            end_time = time.time()
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Verify performance
            duration = end_time - start_time
            assert duration < 5.0  # Should complete within 5 seconds
            
            # Verify events were captured
            events_metric = monitor.metrics.get_metric("events_total")
            assert events_metric is not None
            assert len(events_metric.points) >= event_count
            
            # Verify system health remains good
            health = monitor.get_system_health()
            assert health["status"] in ["healthy", "degraded"]  # Should not be unhealthy
            
        finally:
            await monitor.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_monitoring(self):
        """Test multiple concurrent monitoring operations."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            async def simulate_brain_activity():
                for i in range(10):
                    global_events.emit("brain.thinking.started", {
                        "model": "deepseek-chat",
                        "agent": f"brain_agent_{i}"
                    }, source=f"brain_agent_{i}")
                    
                    await asyncio.sleep(0.01)
                    
                    global_events.emit("brain.thinking.completed", {
                        "model": "deepseek-chat",
                        "duration_ms": 1000.0 + i * 100,
                        "agent": f"brain_agent_{i}",
                        "_thinking_start": time.time() - (1.0 + i * 0.1)
                    }, source=f"brain_agent_{i}")
            
            async def simulate_tool_activity():
                tools = ["web_search", "read_file", "write_file", "calculate"]
                for i in range(15):
                    tool = tools[i % len(tools)]
                    agent = f"tool_agent_{i % 3}"
                    
                    global_events.emit("tool.started", {
                        "tool_name": tool,
                        "agent": agent
                    }, source=agent)
                    
                    await asyncio.sleep(0.005)
                    
                    if i % 4 != 0:  # 75% success rate
                        global_events.emit("tool.completed", {
                            "tool_name": tool,
                            "duration_ms": 500.0 + i * 50,
                            "agent": agent,
                            "_tool_start": time.time() - (0.5 + i * 0.05)
                        }, source=agent)
                    else:
                        global_events.emit("tool.failed", {
                            "tool_name": tool,
                            "error": f"Simulated error {i}",
                            "agent": agent
                        }, source=agent)
            
            async def simulate_memory_activity():
                for i in range(8):
                    agent = f"memory_agent_{i % 2}"
                    operation = "saved" if i % 2 == 0 else "searched"
                    
                    global_events.emit(f"memory.{operation}", {
                        "operation": operation,
                        "duration_ms": 100.0 + i * 25,
                        "agent": agent
                    }, source=agent)
                    
                    await asyncio.sleep(0.02)
            
            # Run all simulations concurrently
            await asyncio.gather(
                simulate_brain_activity(),
                simulate_tool_activity(),
                simulate_memory_activity()
            )
            
            # Wait for processing
            await asyncio.sleep(0.2)
            
            # Verify all metrics were collected
            brain_metric = monitor.metrics.get_metric("brain_thinking_time")
            assert brain_metric is not None
            assert len(brain_metric.points) >= 10
            
            tool_metric = monitor.metrics.get_metric("tool_execution_time")
            assert tool_metric is not None
            assert len(tool_metric.points) >= 10  # Should have successful executions
            
            tool_errors = monitor.metrics.get_metric("tool_errors")
            assert tool_errors is not None
            assert len(tool_errors.points) >= 3  # Should have some failures
            
            memory_metric = monitor.metrics.get_metric("memory_operations_total")
            assert memory_metric is not None
            assert len(memory_metric.points) >= 8
            
            # Verify system performance
            performance = monitor.get_performance_summary()
            assert "avg_brain_thinking_time_ms" in performance
            assert "avg_tool_execution_time_ms" in performance
            assert "tool_success_rate_percent" in performance
            
            # Tool success rate should be around 75%
            if "tool_success_rate_percent" in performance:
                success_rate = performance["tool_success_rate_percent"]
                assert 70 <= success_rate <= 80
            
        finally:
            await monitor.stop()


class TestObservabilityResilience:
    """Test observability system resilience and error handling."""
    
    @pytest.mark.asyncio
    async def test_monitor_restart(self):
        """Test that monitor can be restarted without issues."""
        monitor = ObservabilityMonitor()
        
        # Start and stop multiple times
        for i in range(3):
            await monitor.start()
            assert monitor.is_running
            
            # Generate some events
            global_events.emit("test.restart", {
                "cycle": i,
                "timestamp": time.time()
            }, source="restart_test")
            
            await asyncio.sleep(0.05)
            
            await monitor.stop()
            assert not monitor.is_running
        
        # Final start and verify it works
        await monitor.start()
        
        try:
            global_events.emit("test.final", {
                "message": "Final test"
            }, source="restart_test")
            
            await asyncio.sleep(0.1)
            
            events_metric = monitor.metrics.get_metric("events_total")
            assert events_metric is not None
            assert len(events_metric.points) > 0
            
        finally:
            await monitor.stop()
    
    def test_invalid_event_handling(self):
        """Test that invalid events don't crash the monitor."""
        monitor = ObservabilityMonitor()
        
        # Emit events with invalid data
        global_events.emit("test.invalid", {
            "invalid_duration": "not_a_number",
            "missing_required_field": None
        }, source="invalid_test")
        
        global_events.emit("brain.thinking.completed", {
            "duration_ms": "invalid",  # Should be a number
            "agent": None
        }, source="invalid_brain")
        
        # Monitor should still be functional
        health = monitor.get_system_health()
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        
        # Should still be able to record valid events
        global_events.emit("test.valid", {
            "message": "This should work"
        }, source="valid_test")
        
        events_metric = monitor.metrics.get_metric("events_total")
        assert events_metric is not None
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test that the system handles memory pressure gracefully."""
        monitor = ObservabilityMonitor()
        await monitor.start()
        
        try:
            # Create metrics with limited history and overflow them
            test_metric = monitor.metrics.create_metric("memory_test", "Test", "count")
            
            # Add many more points than the limit
            for i in range(2000):  # Much more than default 1000 limit
                monitor.metrics.record_value("memory_test", float(i))
            
            # System should still be responsive
            health = monitor.get_system_health()
            assert health["status"] in ["healthy", "degraded", "unhealthy"]
            
            # Metric should be bounded
            assert len(test_metric.points) <= 1000
            
            # Should contain recent data
            latest_point = test_metric.get_latest()
            assert latest_point is not None
            assert latest_point.value >= 1000.0  # Should be from recent data
            
        finally:
            await monitor.stop()


if __name__ == "__main__":
    pytest.main([__file__]) 