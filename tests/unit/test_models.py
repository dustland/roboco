"""
Tests for the unified model approach.

These tests verify that models work as both domain models and database models.
"""
import pytest
from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session, select

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole, MessageType
)
from roboco.api.models import (
    ProjectCreate, TaskCreate, MessageCreate
)

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def test_engine():
    """Create a clean database engine for tests."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def test_session(test_engine):
    """Create a new database session for tests."""
    with Session(test_engine) as session:
        yield session


def test_unified_model_project(test_session):
    """Test creating a Project using the unified model."""
    # Create project
    project = Project(
        name="Test Project",
        description="A project for testing the unified model approach",
        meta={"key": "value"}
    )
    
    # Save to database
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    # Verify it was saved correctly
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "A project for testing the unified model approach"
    assert project.meta == {"key": "value"}
    assert project.created_at is not None
    assert project.updated_at is not None
    
    # Modify project
    project.name = "Updated Project Name"
    project.update_timestamp()
    
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    # Verify changes were saved
    assert project.name == "Updated Project Name"


def test_unified_model_task(test_session):
    """Test creating a Task using the unified model."""
    # Create project first
    project = Project(name="Project for Task Test")
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    # Create task
    task = Task(
        title="Test Task",
        description="A task for testing the unified model approach",
        status=TaskStatus.TODO,
        priority="high",
        project_id=project.id,
        meta={"key": "value"},
        tags=["test", "unified"]
    )
    
    # Save to database
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)
    
    # Verify it was saved correctly
    assert task.id is not None
    assert task.title == "Test Task"
    assert task.description == "A task for testing the unified model approach"
    assert task.status == TaskStatus.TODO
    assert task.priority == "high"
    assert task.project_id == project.id
    assert task.meta == {"key": "value"}
    assert task.tags == ["test", "unified"]
    assert task.created_at is not None
    assert task.updated_at is not None
    
    # Mark task as completed
    task.mark_as_completed()
    
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)
    
    # Verify status change
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_unified_model_message(test_session):
    """Test creating a Message using the unified model."""
    # Create project and task first
    project = Project(name="Project for Message Test")
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    task = Task(
        title="Task for Message Test",
        project_id=project.id
    )
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)
    
    # Create message
    message = Message(
        content="Test message content",
        role=MessageRole.USER,
        task_id=task.id,
        type=MessageType.TEXT,
        meta={"key": "value"},
        tool_calls=[{"id": "call_123", "name": "test_tool"}]
    )
    
    # Save to database
    test_session.add(message)
    test_session.commit()
    test_session.refresh(message)
    
    # Verify it was saved correctly
    assert message.id is not None
    assert message.content == "Test message content"
    assert message.role == MessageRole.USER
    assert message.task_id == task.id
    assert message.type == MessageType.TEXT
    assert message.meta == {"key": "value"}
    assert message.tool_calls == [{"id": "call_123", "name": "test_tool"}]
    assert message.timestamp is not None
    
    # Convert to dict for API response
    message_dict = message.to_dict()
    
    # Verify dict has all necessary fields
    assert message_dict["id"] == message.id
    assert message_dict["content"] == message.content
    assert message_dict["role"] == message.role
    assert message_dict["task_id"] == message.task_id
    assert message_dict["type"] == message.type
    assert message_dict["meta"] == message.meta
    assert message_dict["tool_calls"] == message.tool_calls


def test_relationships(test_session):
    """Test the relationships between models."""
    # Create a project
    project = Project(name="Relationship Test Project")
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    # Create a task in the project
    task = Task(
        title="Relationship Test Task",
        project_id=project.id
    )
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)
    
    # Create a message for the task
    message = Message(
        content="Relationship test message",
        role=MessageRole.USER,
        task_id=task.id
    )
    test_session.add(message)
    test_session.commit()
    test_session.refresh(message)
    
    # Test relationships in both directions
    
    # Task to Project relationship
    assert task.project_id == project.id
    assert task.project.id == project.id  # Relationship navigation
    
    # Project to Tasks relationship
    project_tasks = test_session.exec(
        select(Task).where(Task.project_id == project.id)
    ).all()
    assert len(project_tasks) == 1
    assert project_tasks[0].id == task.id
    
    # Task to Messages relationship
    task_messages = test_session.exec(
        select(Message).where(Message.task_id == task.id)
    ).all()
    assert len(task_messages) == 1
    assert task_messages[0].id == message.id


def test_api_model_conversion(test_session):
    """Test converting between API models and DB models."""
    # Create a ProjectCreate API model
    project_create = ProjectCreate(
        name="API Conversion Test Project",
        description="Testing API to DB model conversion",
        meta={"source": "api", "priority": "high"}
    )
    
    # Convert to DB model
    project = project_create.to_db_model()
    
    # Save to database
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    # Verify conversion was correct
    assert project.name == project_create.name
    assert project.description == project_create.description
    assert project.meta == project_create.meta
    
    # Same for TaskCreate
    task_create = TaskCreate(
        title="API Conversion Test Task",
        description="Testing API to DB model conversion for tasks",
        status=TaskStatus.TODO,
        priority="medium",
        project_id=project.id,
        meta={"source": "api"},
        tags=["test", "api"]
    )
    
    # Convert to DB model
    task = task_create.to_db_model()
    
    # Save to database
    test_session.add(task)
    test_session.commit()
    test_session.refresh(task)
    
    # Verify conversion was correct
    assert task.title == task_create.title
    assert task.description == task_create.description
    assert task.status == task_create.status
    assert task.priority == task_create.priority
    assert task.project_id == task_create.project_id
    assert task.meta == task_create.meta
    assert task.tags == task_create.tags 