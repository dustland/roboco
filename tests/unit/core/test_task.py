"""
Unit tests for Task component.

Tests task creation, management, and lifecycle functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from roboco.core.task import Task, TaskConfig
from roboco.core.brain import ChatHistory, Message


class TestTaskConfig:
    """Test TaskConfig dataclass."""
    
    def test_task_config_creation(self):
        """Test basic task config creation."""
        config = TaskConfig(
            name="Test Task",
            description="Test task for unit testing"
        )
        
        assert config.name == "Test Task"
        assert config.description == "Test task for unit testing"
        assert config.max_iterations == 10  # default
        assert config.timeout is None  # default
        assert config.metadata == {}  # default
    
    def test_task_config_with_custom_values(self):
        """Test task config with custom values."""
        config = TaskConfig(
            name="Custom Task",
            description="Custom description",
            max_iterations=20,
            timeout=300,
            metadata={"key": "value"}
        )
        
        assert config.name == "Custom Task"
        assert config.description == "Custom description"
        assert config.max_iterations == 20
        assert config.timeout == 300
        assert config.metadata == {"key": "value"}


class TestTask:
    """Test Task class."""
    
    def test_task_creation_basic(self):
        """Test basic task creation."""
        config = TaskConfig(
            name="Test Task",
            description="Test task for unit testing"
        )
        task = Task(config)
        
        assert task.description == "Test task for unit testing"
        assert task.status == "created"
        assert isinstance(task.task_id, str)
        assert len(task.task_id) == 8  # Short ID format
        assert isinstance(task.created_at, datetime)
        assert task.config_path == ""
    
    def test_task_creation_with_dict_config(self):
        """Test task creation with dict config."""
        config_dict = {
            "name": "Dict Task",
            "description": "Task created from dict",
            "max_iterations": 15
        }
        task = Task(config_dict)
        
        assert task.description == "Task created from dict"
        assert task.config.max_iterations == 15
    
    def test_task_creation_with_config_path(self):
        """Test task creation with config path."""
        config = TaskConfig(
            name="Configured Task",
            description="Configured task"
        )
        task = Task(config, config_path="config/test.yaml")
        
        assert task.description == "Configured task"
        assert task.config_path == "config/test.yaml"
    
    def test_task_id_uniqueness(self):
        """Test that task IDs are unique."""
        config1 = TaskConfig(name="Task 1", description="First task")
        config2 = TaskConfig(name="Task 2", description="Second task")
        
        task1 = Task(config1)
        task2 = Task(config2)
        
        assert task1.task_id != task2.task_id
    
    def test_task_metadata_handling(self):
        """Test task metadata handling."""
        config = TaskConfig(
            name="Metadata Task",
            description="Task with metadata",
            metadata={"key": "value", "number": 42}
        )
        task = Task(config)
        
        assert task.metadata["key"] == "value"
        assert task.metadata["number"] == 42
    
    def test_task_get_info(self):
        """Test getting task info."""
        config = TaskConfig(
            name="Info Task",
            description="Task for info testing"
        )
        task = Task(config)
        
        info = task.get_info()
        
        assert info.task_id == task.task_id
        assert info.description == "Task for info testing"
        assert info.status == "created"
        assert isinstance(info.created_at, str)
        assert isinstance(info.updated_at, str)
    
    def test_task_string_representation(self):
        """Test task string representations."""
        config = TaskConfig(
            name="String Task",
            description="String representation test"
        )
        task = Task(config)
        
        # The actual string representation depends on implementation
        # Just verify it contains key information
        task_str = str(task)
        assert task.task_id in task_str or "Task" in task_str


class TestTaskLifecycle:
    """Test task lifecycle management."""
    
    @pytest.mark.asyncio
    async def test_task_start(self):
        """Test starting a task."""
        config = TaskConfig(
            name="Start Task",
            description="Task to test starting"
        )
        task = Task(config)
        
        assert task.status == "created"
        
        # Mock the team collaboration
        with patch('roboco.core.task.create_team') as mock_create_team, \
             patch('roboco.core.task.create_assistant_agent') as mock_create_agent:
            
            mock_agent = MagicMock()
            mock_create_agent.return_value = mock_agent
            
            mock_team = AsyncMock()
            mock_chat_history = ChatHistory(task_id=task.task_id)
            mock_chat_history.add_message(Message(
                content="Task completed successfully",
                sender="Assistant",
                role="assistant"
            ))
            mock_team.start_conversation.return_value = mock_chat_history
            mock_create_team.return_value = mock_team
            
            result = await task.start()
            
            # Task should be completed after running the collaboration
            assert task.status == "completed"
            assert result.success is True
            assert isinstance(result.conversation_history, ChatHistory)
    
    def test_task_stop(self):
        """Test stopping a task."""
        config = TaskConfig(
            name="Stop Task",
            description="Task to test stopping"
        )
        task = Task(config)
        
        # Start the task first (mock the start)
        task._update_status("running")
        
        result = task.stop()
        
        assert result is True
        assert task.status == "stopped"
    
    def test_task_delete(self):
        """Test deleting a task."""
        config = TaskConfig(
            name="Delete Task",
            description="Task to test deletion"
        )
        task = Task(config)
        
        result = task.delete()
        
        assert result is True
        # Note: The actual deletion behavior depends on implementation


class TestTaskEventHandling:
    """Test task event handling."""
    
    def test_task_event_registration(self):
        """Test registering event handlers."""
        config = TaskConfig(
            name="Event Task",
            description="Task for event testing"
        )
        task = Task(config)
        
        # Create a mock handler
        handler_called = []
        
        def test_handler(event):
            handler_called.append(event)
        
        # Register handler
        task.on("task.status_changed", test_handler)
        
        # Trigger status change
        task._update_status("running")
        
        # Verify handler was called
        assert len(handler_called) == 1
        assert handler_called[0]["event_type"] == "task.status_changed"
        assert handler_called[0]["data"]["new_status"] == "running"
    
    def test_task_event_unregistration(self):
        """Test unregistering event handlers."""
        config = TaskConfig(
            name="Event Task",
            description="Task for event testing"
        )
        task = Task(config)
        
        handler_called = []
        
        def test_handler(event):
            handler_called.append(event)
        
        # Register and then unregister handler
        task.on("task.status_changed", test_handler)
        task.off("task.status_changed", test_handler)
        
        # Trigger status change
        task._update_status("running")
        
        # Verify handler was not called
        assert len(handler_called) == 0


class TestTaskChatSession:
    """Test task chat session functionality."""
    
    def test_task_get_chat(self):
        """Test getting chat session."""
        config = TaskConfig(
            name="Chat Task",
            description="Task for chat testing"
        )
        task = Task(config)
        
        chat_session = task.get_chat()
        
        assert chat_session is not None
        assert chat_session.task == task
    
    @pytest.mark.asyncio
    async def test_chat_session_send_message_not_running(self):
        """Test sending message when task is not running."""
        config = TaskConfig(
            name="Chat Task",
            description="Task for chat testing"
        )
        task = Task(config)
        chat_session = task.get_chat()
        
        # Task is in 'created' status, should raise error
        with pytest.raises(RuntimeError, match="Cannot send message to task with status: created"):
            await chat_session.send_message("Test message")
    
    @pytest.mark.asyncio
    async def test_chat_session_send_message_running(self):
        """Test sending message when task is running."""
        config = TaskConfig(
            name="Chat Task",
            description="Task for chat testing"
        )
        task = Task(config)
        chat_session = task.get_chat()
        
        # Set task to running status
        task._update_status("running")
        
        result = await chat_session.send_message("Test message", sender="user")
        
        assert result["success"] is True
        assert "message_id" in result
        
        # Check chat history
        history = chat_session.get_chat_history()
        assert len(history) == 1
        assert history[0]["message"] == "Test message"
        assert history[0]["sender"] == "user"
