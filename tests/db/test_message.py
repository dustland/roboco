"""
Tests for Message database operations.

This module tests the database operations for the Message model.
"""
import pytest
from datetime import datetime

from roboco.core.models import Message, MessageRole, MessageType
from roboco.api.models import MessageCreate
from roboco.db import service as db_service
from tests.fixtures.utils import count_rows, get_by_id


class TestMessageDB:
    """Tests for the Message database operations."""

    def test_create_message(self, db_engine, db_session, created_task, sample_message_data):
        """Test creating a message associated with a task."""
        message_data = sample_message_data.model_copy(update={"task_id": created_task.id})
        
        # Create a message
        message = db_service.create_message(created_task.id, message_data)
        
        # Verify it was created with the correct data
        assert isinstance(message, Message)
        assert message.id is not None
        assert message.content == message_data.content
        assert message.role == message_data.role
        assert message.task_id == created_task.id
        assert message.type == message_data.type
        assert message.meta == message_data.meta
        assert message.timestamp is not None
        
        # Verify it exists in the database
        db_message = get_by_id(db_session, Message, message.id)
        assert db_message is not None
        assert db_message.content == message_data.content

    def test_get_message(self, db_engine, db_session, created_message):
        """Test retrieving a message by ID."""
        # Retrieve the message
        retrieved_message = db_service.get_message(created_message.id)
        
        # Verify it was retrieved correctly
        assert isinstance(retrieved_message, Message)
        assert retrieved_message.id == created_message.id
        assert retrieved_message.content == created_message.content
        assert retrieved_message.role == created_message.role
        assert retrieved_message.task_id == created_message.task_id
        assert retrieved_message.type == created_message.type

    def test_get_messages_by_task(self, db_engine, db_session, created_task, sample_message_data):
        """Test retrieving all messages for a task."""
        # Create multiple messages
        message_data = sample_message_data.model_copy(update={"task_id": created_task.id})
        message1 = db_service.create_message(created_task.id, message_data)
        
        message2 = db_service.create_message(
            created_task.id,
            MessageCreate(
                content="Another test message",
                role=MessageRole.ASSISTANT,
                task_id=created_task.id,
                type=MessageType.TEXT
            )
        )
        
        # Retrieve messages for the task
        messages = db_service.get_messages_by_task(created_task.id)
        
        # Verify we got the right messages
        assert len(messages) == 2
        assert all(isinstance(msg, Message) for msg in messages)
        assert all(msg.task_id == created_task.id for msg in messages)
        
        # Verify both messages are in the result
        message_ids = [msg.id for msg in messages]
        assert message1.id in message_ids
        assert message2.id in message_ids

    def test_delete_message(self, db_engine, db_session, created_message):
        """Test deleting a message."""
        # Delete the message
        success = db_service.delete_message(created_message.id)
        
        # Verify it was deleted
        assert success is True
        
        # Verify we can't retrieve it anymore
        assert db_service.get_message(created_message.id) is None
        assert get_by_id(db_session, Message, created_message.id) is None

    def test_message_with_tool_calls(self, db_engine, db_session, created_task):
        """Test creating and retrieving a message with tool calls."""
        # Create a message with tool calls
        message = db_service.create_message(
            created_task.id,
            MessageCreate(
                content="Message with tool calls",
                role=MessageRole.ASSISTANT,
                task_id=created_task.id,
                type=MessageType.TOOL_CALL,
                meta={"key": "value"},
                tool_calls=[{
                    "id": "call_123",
                    "name": "test_tool",
                    "arguments": {"arg1": "value1"}
                }]
            )
        )
        
        # Verify it was created with the correct data
        assert message.type == MessageType.TOOL_CALL
        assert message.tool_calls == [
            {
                "id": "call_123",
                "name": "test_tool",
                "arguments": {"arg1": "value1"}
            }
        ]
        
        # Retrieve the message and verify tool calls are preserved
        retrieved_message = db_service.get_message(message.id)
        assert retrieved_message.tool_calls == message.tool_calls 