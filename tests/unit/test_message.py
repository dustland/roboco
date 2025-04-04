"""
Tests for the Message model and related functionality.

This module tests the core Message model functionality.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from sqlmodel import Session, select

from roboco.core.models import (
    Message, Task, Project,
    MessageRole, MessageType, TaskStatus
)

# Import test fixtures from conftest
from tests.conftest import test_engine, test_session


class TestMessageCreation:
    """Tests for creating Message objects."""
    
    def test_create_message(self):
        """Test creating a simple message."""
        # Create a message
        message = Message(
            content="Test message content",
            role=MessageRole.USER,
            type=MessageType.TEXT
        )
        
        # Verify basic properties
        assert message.content == "Test message content"
        assert message.role == MessageRole.USER
        assert message.type == MessageType.TEXT
        assert message.id is not None
        assert message.timestamp is not None
        
    def test_message_with_tool_calls(self):
        """Test creating a message with tool call information."""
        # Create tool calls data
        tool_calls = [
            {
                "id": "call_123",
                "name": "test_tool",
                "arguments": {"arg1": "value1"}
            }
        ]
        
        # Create a message with tool calls
        message = Message(
            content="Tool call message",
            role=MessageRole.ASSISTANT,
            type=MessageType.TOOL_CALL,
            tool_calls=tool_calls
        )
        
        # Verify tool calls data
        assert message.type == MessageType.TOOL_CALL
        assert len(message.tool_calls) == 1
        assert message.tool_calls[0]["id"] == "call_123"
        assert message.tool_calls[0]["name"] == "test_tool"
        
    def test_message_with_meta(self):
        """Test creating a message with metadata."""
        # Create a message with metadata
        meta_data = {
            "source": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "tags": ["test", "meta"]
        }
        
        message = Message(
            content="Message with metadata",
            role=MessageRole.SYSTEM,
            type=MessageType.TEXT,
            meta=meta_data
        )
        
        # Verify metadata
        assert message.meta is not None
        assert message.meta["source"] == "test"
        assert "timestamp" in message.meta
        assert message.meta["tags"] == ["test", "meta"]


class TestMessagePersistence:
    """Tests for persisting Message objects to database."""
    
    def test_message_persistence(self, test_session):
        """Test persisting a message to the database."""
        # Create a project and task first
        project = Project(name="Test Project")
        test_session.add(project)
        test_session.commit()
        test_session.refresh(project)
        
        task = Task(
            title="Test Task",
            project_id=project.id
        )
        test_session.add(task)
        test_session.commit()
        test_session.refresh(task)
        
        # Create and persist a message
        message = Message(
            content="Persistent message",
            role=MessageRole.USER,
            type=MessageType.TEXT,
            task_id=task.id
        )
        test_session.add(message)
        test_session.commit()
        test_session.refresh(message)
        
        # Retrieve the message and verify
        db_message = test_session.exec(
            select(Message).where(Message.id == message.id)
        ).first()
        
        assert db_message is not None
        assert db_message.id == message.id
        assert db_message.content == "Persistent message"
        assert db_message.task_id == task.id
        
    def test_message_serialization(self, test_session):
        """Test message serialization (to_dict method)."""
        # Create a message with complex data
        tool_calls = [{"id": "call_123", "name": "test_tool"}]
        meta_data = {"source": "test"}
        
        message = Message(
            content="Serialization test",
            role=MessageRole.ASSISTANT,
            type=MessageType.TOOL_CALL,
            tool_calls=tool_calls,
            meta=meta_data,
            timestamp=datetime.utcnow()
        )
        
        # Call to_dict method
        result = message.to_dict()
        
        # Verify serialization
        assert result["content"] == "Serialization test"
        assert result["role"] == MessageRole.ASSISTANT
        assert result["type"] == MessageType.TOOL_CALL
        assert "tool_calls" in result
        assert result["tool_calls"] == tool_calls
        assert "meta" in result
        assert result["meta"] == meta_data
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)  # Should be ISO format 