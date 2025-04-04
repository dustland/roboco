"""
Database test fixtures.

This module provides fixtures for database tests.
"""
import pytest

from roboco.core.models import Project, Task, Message, TaskStatus, MessageRole, MessageType
from roboco.api.models import ProjectCreate, TaskCreate, MessageCreate

# Import fixtures from the main conftest
from tests.conftest import db_engine, db_session, clean_db


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
        meta={"effort": "medium"}
    )


@pytest.fixture
def sample_message_data() -> MessageCreate:
    """Create sample message data for testing."""
    return MessageCreate(
        content="Test message",
        role=MessageRole.USER,
        type=MessageType.TEXT
    )


@pytest.fixture
def created_project(db_session, sample_project_data):
    """Create a project in the database."""
    project = Project(**sample_project_data.model_dump())
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def created_task(db_session, created_project, sample_task_data):
    """Create a task in the database."""
    task_data = sample_task_data.model_dump()
    task_data["project_id"] = created_project.id
    task = Task(**task_data)
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


@pytest.fixture
def created_message(db_session, created_task, sample_message_data):
    """Create a message in the database."""
    message_data = sample_message_data.model_dump()
    message_data["task_id"] = created_task.id
    message = Message(**message_data)
    db_session.add(message)
    db_session.commit()
    db_session.refresh(message)
    return message 