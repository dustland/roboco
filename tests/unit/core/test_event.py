"""
Tests for the Event and EventBus classes.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from roboco.core.event import Event, EventBus, EventType, GlobalEventBus
from roboco.core.agent import Agent, AgentConfig


class TestEvent:
    """Test Event class."""
    
    def test_event_creation(self):
        """Test Event creation with required fields."""
        event = Event(
            event_type="test.event",
            data={"key": "value"},
            source="test_source"
        )
        
        assert event.event_type == "test.event"
        assert event.data == {"key": "value"}
        assert event.source == "test_source"
        assert isinstance(event.timestamp, datetime)
        assert isinstance(event.event_id, str)
        assert len(event.event_id) > 0
    
    def test_event_creation_with_custom_values(self):
        """Test Event creation with custom timestamp and ID."""
        timestamp = datetime.now()
        event_id = "custom_id"
        
        event = Event(
            event_type="custom.event",
            data={"custom": "data"},
            source="custom_source",
            timestamp=timestamp,
            event_id=event_id
        )
        
        assert event.timestamp == timestamp
        assert event.event_id == event_id
    
    def test_event_to_dict(self):
        """Test Event to_dict conversion."""
        timestamp = datetime.now()
        event = Event(
            event_type="test.event",
            data={"key": "value"},
            source="test_source",
            timestamp=timestamp,
            event_id="test_id"
        )
        
        result = event.to_dict()
        
        assert result["event_type"] == "test.event"
        assert result["data"] == {"key": "value"}
        assert result["source"] == "test_source"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["event_id"] == "test_id"
    
    def test_event_from_dict(self):
        """Test Event from_dict creation."""
        timestamp = datetime.now()
        data = {
            "event_type": "test.event",
            "data": {"key": "value"},
            "source": "test_source",
            "timestamp": timestamp.isoformat(),
            "event_id": "test_id"
        }
        
        event = Event.from_dict(data)
        
        assert event.event_type == "test.event"
        assert event.data == {"key": "value"}
        assert event.source == "test_source"
        assert event.timestamp == timestamp
        assert event.event_id == "test_id"
    
    def test_event_from_dict_with_datetime_object(self):
        """Test Event from_dict with datetime object."""
        timestamp = datetime.now()
        data = {
            "event_type": "test.event",
            "data": {"key": "value"},
            "source": "test_source",
            "timestamp": timestamp,  # datetime object, not string
            "event_id": "test_id"
        }
        
        event = Event.from_dict(data)
        assert event.timestamp == timestamp


class TestEventType:
    """Test EventType enum."""
    
    def test_event_type_values(self):
        """Test EventType enum values."""
        assert EventType.AGENT_CREATED.value == "agent.created"
        assert EventType.AGENT_ACTIVATED.value == "agent.activated"
        assert EventType.AGENT_DEACTIVATED.value == "agent.deactivated"
        assert EventType.AGENT_RESET.value == "agent.reset"
        
        assert EventType.MESSAGE_SENT.value == "message.sent"
        assert EventType.MESSAGE_RECEIVED.value == "message.received"
        
        assert EventType.TOOL_EXECUTED.value == "tool.executed"
        assert EventType.TOOL_FAILED.value == "tool.failed"
        
        assert EventType.MEMORY_SAVED.value == "memory.saved"
        assert EventType.MEMORY_SEARCHED.value == "memory.searched"
        
        assert EventType.TEAM_CREATED.value == "team.created"
        assert EventType.TEAM_CONVERSATION_STARTED.value == "team.conversation.started"
        assert EventType.TEAM_CONVERSATION_ENDED.value == "team.conversation.ended"
        assert EventType.TEAM_SPEAKER_CHANGED.value == "team.speaker.changed"
        
        assert EventType.CUSTOM.value == "custom"


class TestEventBus:
    """Test EventBus class."""
    
    def test_event_bus_initialization(self, mock_agent):
        """Test EventBus initialization."""
        event_bus = EventBus(mock_agent)
        
        assert event_bus.agent == mock_agent
        assert event_bus.listeners == {}
        assert event_bus.event_history == []
        assert event_bus.max_history == 1000
    
    def test_register_listener(self, mock_agent):
        """Test registering event listeners."""
        event_bus = EventBus(mock_agent)
        
        def callback1(event):
            pass
        
        def callback2(event):
            pass
        
        # Register listeners
        event_bus.on("test.event", callback1)
        event_bus.on("test.event", callback2)
        event_bus.on("other.event", callback1)
        
        assert len(event_bus.listeners["test.event"]) == 2
        assert callback1 in event_bus.listeners["test.event"]
        assert callback2 in event_bus.listeners["test.event"]
        assert len(event_bus.listeners["other.event"]) == 1
        assert callback1 in event_bus.listeners["other.event"]
    
    def test_unregister_listener(self, mock_agent):
        """Test unregistering event listeners."""
        event_bus = EventBus(mock_agent)
        
        def callback1(event):
            pass
        
        def callback2(event):
            pass
        
        # Register and then unregister
        event_bus.on("test.event", callback1)
        event_bus.on("test.event", callback2)
        
        event_bus.off("test.event", callback1)
        
        assert len(event_bus.listeners["test.event"]) == 1
        assert callback1 not in event_bus.listeners["test.event"]
        assert callback2 in event_bus.listeners["test.event"]
        
        # Try to unregister non-existent callback (should not raise error)
        event_bus.off("test.event", callback1)
        event_bus.off("non.existent", callback1)
    
    def test_emit_event(self, mock_agent):
        """Test emitting events."""
        event_bus = EventBus(mock_agent)
        
        # Mock callbacks
        callback1 = Mock()
        callback2 = Mock()
        
        event_bus.on("test.event", callback1)
        event_bus.on("test.event", callback2)
        
        # Emit event
        test_data = {"key": "value"}
        event_bus.emit("test.event", test_data)
        
        # Verify callbacks were called
        assert callback1.call_count == 1
        assert callback2.call_count == 1
        
        # Verify event was added to history
        assert len(event_bus.event_history) == 1
        event = event_bus.event_history[0]
        assert event.event_type == "test.event"
        assert event.data == test_data
        assert event.source == "test_agent"
    
    def test_emit_event_callback_error(self, mock_agent):
        """Test emitting events with callback errors."""
        event_bus = EventBus(mock_agent)
        
        def failing_callback(event):
            raise Exception("Callback error")
        
        def working_callback(event):
            pass
        
        working_mock = Mock(side_effect=working_callback)
        
        event_bus.on("test.event", failing_callback)
        event_bus.on("test.event", working_mock)
        
        # Should not raise exception, but working callback should still be called
        event_bus.emit("test.event", {})
        
        working_mock.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_emit_async_event(self, mock_agent):
        """Test emitting events asynchronously."""
        event_bus = EventBus(mock_agent)
        
        # Mock async and sync callbacks
        async_callback = AsyncMock()
        sync_callback = Mock()
        
        event_bus.on("test.event", async_callback)
        event_bus.on("test.event", sync_callback)
        
        # Emit async event
        test_data = {"key": "value"}
        await event_bus.emit_async("test.event", test_data)
        
        # Verify callbacks were called
        async_callback.assert_called_once()
        sync_callback.assert_called_once()
        
        # Verify event was added to history
        assert len(event_bus.event_history) == 1
        event = event_bus.event_history[0]
        assert event.event_type == "test.event"
        assert event.data == test_data
    
    def test_get_events(self, mock_agent):
        """Test getting event history."""
        event_bus = EventBus(mock_agent)
        
        # Add some events
        event_bus.emit("event.type1", {"data": 1})
        event_bus.emit("event.type2", {"data": 2})
        event_bus.emit("event.type1", {"data": 3})
        
        # Get all events
        all_events = event_bus.get_events()
        assert len(all_events) == 3
        
        # Get events by type
        type1_events = event_bus.get_events("event.type1")
        assert len(type1_events) == 2
        assert all(e.event_type == "event.type1" for e in type1_events)
        
        # Get limited events
        limited_events = event_bus.get_events(limit=2)
        assert len(limited_events) == 2
        
        # Get unlimited events
        unlimited_events = event_bus.get_events(limit=0)
        assert len(unlimited_events) == 3
    
    def test_get_recent_events(self, mock_agent):
        """Test getting recent events."""
        event_bus = EventBus(mock_agent)
        
        # Add old event
        old_event = Event("old.event", {}, "test_agent", 
                         timestamp=datetime.now() - timedelta(hours=2))
        event_bus.event_history.append(old_event)
        
        # Add recent event
        event_bus.emit("recent.event", {})
        
        # Get recent events (last 60 minutes)
        recent_events = event_bus.get_recent_events(minutes=60)
        
        assert len(recent_events) == 1
        assert recent_events[0].event_type == "recent.event"
    
    def test_clear_history(self, mock_agent):
        """Test clearing event history."""
        event_bus = EventBus(mock_agent)
        
        # Add some events
        event_bus.emit("test.event1", {})
        event_bus.emit("test.event2", {})
        
        assert len(event_bus.event_history) == 2
        
        # Clear history
        event_bus.clear_history()
        
        assert len(event_bus.event_history) == 0
    
    def test_history_cleanup(self, mock_agent):
        """Test automatic history cleanup."""
        event_bus = EventBus(mock_agent)
        event_bus.max_history = 3
        
        # Add events beyond limit
        for i in range(5):
            event_bus.emit(f"test.event{i}", {"index": i})
        
        # Should keep only the most recent events
        assert len(event_bus.event_history) == 3
        
        # Verify the kept events are the most recent ones
        event_data = [e.data["index"] for e in event_bus.event_history]
        assert event_data == [2, 3, 4]
    
    def test_get_stats_empty(self, mock_agent):
        """Test getting statistics with empty history."""
        event_bus = EventBus(mock_agent)
        
        stats = event_bus.get_stats()
        
        assert stats["total_events"] == 0
        assert stats["event_types"] == {}
        assert stats["oldest_event"] is None
        assert stats["newest_event"] is None
    
    def test_get_stats_with_events(self, mock_agent):
        """Test getting statistics with events."""
        event_bus = EventBus(mock_agent)
        
        # Add listeners
        event_bus.on("test.event", lambda e: None)
        event_bus.on("test.event", lambda e: None)
        event_bus.on("other.event", lambda e: None)
        
        # Add events
        event_bus.emit("test.event", {})
        event_bus.emit("test.event", {})
        event_bus.emit("other.event", {})
        
        stats = event_bus.get_stats()
        
        assert stats["total_events"] == 3
        assert stats["event_types"]["test.event"] == 2
        assert stats["event_types"]["other.event"] == 1
        assert stats["oldest_event"] is not None
        assert stats["newest_event"] is not None
        assert stats["active_listeners"]["test.event"] == 2
        assert stats["active_listeners"]["other.event"] == 1


class TestGlobalEventBus:
    """Test GlobalEventBus singleton."""
    
    def test_singleton_pattern(self):
        """Test that GlobalEventBus is a singleton."""
        bus1 = GlobalEventBus()
        bus2 = GlobalEventBus()
        
        assert bus1 is bus2
    
    def test_global_event_emission(self):
        """Test global event emission."""
        bus = GlobalEventBus()
        
        # Clear any existing history
        bus.event_history.clear()
        bus.listeners.clear()
        
        callback = Mock()
        bus.on("global.test", callback)
        
        bus.emit("global.test", {"global": "data"}, source="test_source")
        
        callback.assert_called_once()
        
        # Verify event in history
        assert len(bus.event_history) == 1
        event = bus.event_history[0]
        assert event.event_type == "global.test"
        assert event.data == {"global": "data"}
        assert event.source == "test_source" 