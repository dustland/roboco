"""
Database fixtures for testing.

This module provides fixtures for database testing to be shared across multiple test modules.
"""
import pytest
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator

from roboco.core.models import Project, Task, Message, TaskStatus, MessageRole, MessageType
from roboco.api.models import ProjectCreate, TaskCreate, MessageCreate
from roboco.db import service as db_service

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a clean database engine for each test."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    
    # Store original function
    original_get_session = db_service.get_session
    
    # Monkey patch the get_session function to use our test database
    db_service.get_session = lambda: Session(engine)
    
    yield engine
    
    # Clean up
    SQLModel.metadata.drop_all(engine)
    
    # Restore original function
    db_service.get_session = original_get_session


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test."""
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def sample_project_data() -> ProjectCreate:
    """Create sample project data for testing."""
    return ProjectCreate(
        name="Test Project",
        description="A project for testing",
        meta={"key": "value"}
    )


@pytest.fixture
def sample_task_data() -> TaskCreate:
    """Create sample task data for testing."""
    return TaskCreate(
        title="Test Task",
        description="A task for testing",
        status=TaskStatus.TODO,
        priority="medium",
        meta={"key": "value"}
    )


@pytest.fixture
def sample_message_data() -> MessageCreate:
    """Create sample message data for testing."""
    return MessageCreate(
        content="Test message content",
        role=MessageRole.USER,
        task_id="placeholder",  # Will be replaced in tests
        type=MessageType.TEXT,
        meta={"key": "value"}
    )


@pytest.fixture
def created_project(db_engine, sample_project_data) -> Project:
    """Create and return a project for testing."""
    return db_service.create_project(sample_project_data)


@pytest.fixture
def created_task(db_engine, created_project, sample_task_data) -> Task:
    """Create and return a task for testing."""
    task_data = sample_task_data
    return db_service.create_task(created_project.id, task_data)


@pytest.fixture
def created_message(db_engine, created_task, sample_message_data) -> Message:
    """Create and return a message for testing."""
    message_data = sample_message_data.model_copy(update={"task_id": created_task.id})
    return db_service.create_message(created_task.id, message_data) 