"""
Tests for API models.

This module contains tests for the Pydantic models used in the API layer.
"""
import pytest
from datetime import datetime
from uuid import uuid4

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole, MessageType
)
from roboco.api.models import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    TaskCreate, TaskUpdate, TaskResponse,
    MessageCreate, MessageResponse
)

# Import fixtures from conftest.py
from tests.conftest import test_engine, test_session


class TestProjectAPIModels:
    """Tests for Project API models."""
    
    def test_project_create_to_db_model(self, test_engine):
        """Test converting ProjectCreate to a DB model."""
        # Create a ProjectCreate instance
        project_data = ProjectCreate(
            name="Test Project",
            description="A project for testing",
            meta={"key": "value"}
        )
        
        # Convert to DB model
        project = project_data.to_db_model()
        
        # Verify conversion
        assert project.name == project_data.name
        assert project.description == project_data.description
        assert project.meta == project_data.meta
        assert project.id is not None
        assert project.created_at is not None
        assert project.updated_at is not None
    
    def test_project_response_from_db_model(self, test_session):
        """Test converting a DB model to ProjectResponse."""
        # Create a Project instance
        project = Project(
            id=str(uuid4())[:8],
            name="Test Project",
            description="A project for testing",
            meta={"key": "value"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Convert to API response model
        response = ProjectResponse.from_db_model(project)
        
        # Verify conversion
        assert response.id == project.id
        assert response.name == project.name
        assert response.description == project.description
        assert response.meta == project.meta
        assert response.created_at == project.created_at.isoformat()
        assert response.updated_at == project.updated_at.isoformat()


class TestTaskAPIModels:
    """Tests for Task API models."""
    
    def test_task_create_to_db_model(self, test_engine):
        """Test converting TaskCreate to a DB model."""
        # Create a TaskCreate instance
        task_data = TaskCreate(
            title="Test Task",
            description="A task for testing",
            status=TaskStatus.TODO,
            priority="high",
            project_id="proj123",
            meta={"key": "value"},
            tags=["tag1", "tag2"]
        )
        
        # Convert to DB model
        task = task_data.to_db_model()
        
        # Verify conversion
        assert task.title == task_data.title
        assert task.description == task_data.description
        assert task.status == task_data.status
        assert task.priority == task_data.priority
        assert task.project_id == task_data.project_id
        assert task.meta == task_data.meta
        assert task.tags == task_data.tags
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None
    
    def test_task_response_from_db_model(self, test_session):
        """Test converting a DB model to TaskResponse."""
        # Create a Task instance
        task = Task(
            id=str(uuid4())[:8],
            title="Test Task",
            description="A task for testing",
            status=TaskStatus.TODO,
            priority="high",
            project_id="proj123",
            meta={"key": "value"},
            tags=["tag1", "tag2"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Convert to API response model
        response = TaskResponse.from_db_model(task)
        
        # Verify conversion
        assert response.id == task.id
        assert response.title == task.title
        assert response.description == task.description
        assert response.status == task.status
        assert response.priority == task.priority
        assert response.project_id == task.project_id
        assert response.meta == task.meta
        assert response.tags == task.tags
        assert response.created_at == task.created_at.isoformat()
        assert response.updated_at == task.updated_at.isoformat()


class TestMessageAPIModels:
    """Tests for Message API models."""
    
    def test_message_create_to_db_model(self, test_engine):
        """Test converting MessageCreate to a DB model."""
        # Create a MessageCreate instance
        message_data = MessageCreate(
            content="Test message",
            role=MessageRole.USER,
            task_id="task123",
            type=MessageType.TEXT,
            meta={"key": "value"}
        )
        
        # Convert to DB model
        message = message_data.to_db_model()
        
        # Verify conversion
        assert message.content == message_data.content
        assert message.role == message_data.role
        assert message.task_id == message_data.task_id
        assert message.type == message_data.type
        assert message.meta == message_data.meta
        assert message.id is not None
        assert message.timestamp is not None
    
    def test_message_response_from_db_model(self, test_session):
        """Test converting a DB model to MessageResponse."""
        # Create a Message instance
        message = Message(
            id=str(uuid4())[:8],
            content="Test message",
            role=MessageRole.USER,
            task_id="task123",
            type=MessageType.TEXT,
            meta={"key": "value"},
            timestamp=datetime.utcnow()
        )
        
        # Convert to API response model
        response = MessageResponse.from_db_model(message)
        
        # Verify conversion
        assert response.id == message.id
        assert response.content == message.content
        assert response.role == message.role
        assert response.task_id == message.task_id
        assert response.type == message.type
        assert response.meta == message.meta
        assert response.timestamp == message.timestamp.isoformat() 