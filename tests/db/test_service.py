"""
Tests for the database service layer.

These tests verify that the database service functions properly interact
with the unified models and handle operations correctly.
"""
import pytest
import asyncio
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine, text
from typing import Dict, Any, Optional, List, Generator

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole
)
from roboco.api.models import (
    ProjectCreate, TaskCreate, MessageCreate
)
from roboco.db import service as db_service
from roboco.db import get_session

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a clean database engine for each test."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    
    # Monkey patch the get_session function to use our test database
    original_get_session = db_service.get_session
    db_service.get_session = lambda: Session(engine)
    
    yield engine
    
    # Clean up
    SQLModel.metadata.drop_all(engine)
    db_service.get_session = original_get_session


@pytest.fixture
def sample_project_data() -> ProjectCreate:
    """Create sample project data for testing."""
    return ProjectCreate(
        name="Test Project",
        description="A project for testing",
        meta={"key": "value"}  # Updated from project_metadata to meta
    )


@pytest.fixture
def sample_task_data() -> TaskCreate:
    """Create sample task data for testing."""
    return TaskCreate(
        title="Test Task",
        description="A task for testing",
        status=TaskStatus.TODO,
        priority="medium",
        meta={"key": "value"}  # Updated from task_metadata to meta
    )


@pytest.fixture
def sample_message_data() -> MessageCreate:
    """Create sample message data for testing."""
    return MessageCreate(
        content="Test message content",
        role=MessageRole.USER,
        type="text",
        meta={"key": "value"}
    )


def test_create_project(db_engine, sample_project_data):
    """Test creating a project."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Verify it was created with the correct data
    assert isinstance(project, Project)
    assert project.id is not None
    assert project.name == sample_project_data.name
    assert project.description == sample_project_data.description
    assert project.meta == sample_project_data.meta  # Updated from project_metadata to meta
    assert project.created_at is not None
    assert project.updated_at is not None


def test_get_project(db_engine, sample_project_data):
    """Test retrieving a project by ID."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Retrieve the project
    retrieved_project = db_service.get_project(project.id)
    
    # Verify it was retrieved correctly
    assert isinstance(retrieved_project, Project)
    assert retrieved_project.id == project.id
    assert retrieved_project.name == project.name
    assert retrieved_project.description == project.description


def test_get_all_projects(db_engine, sample_project_data):
    """Test retrieving all projects."""
    # Create multiple projects
    project1 = db_service.create_project(sample_project_data)
    project2 = db_service.create_project(
        ProjectCreate(
            name="Test Project 2",
            description="Another project for testing"
        )
    )
    
    # Retrieve all projects
    projects = db_service.get_all_projects()
    
    # Verify all projects were retrieved
    assert len(projects) == 2
    assert all(isinstance(project, Project) for project in projects)
    assert all(project.id is not None for project in projects)
    assert all(project.name is not None for project in projects)


def test_update_project(db_engine, sample_project_data):
    """Test updating a project."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Update the project
    updated_project = db_service.update_project(
        project.id,
        ProjectCreate(
            name="Updated Project Name",
            description="Updated description"
        )
    )
    
    # Verify it was updated
    assert isinstance(updated_project, Project)
    assert updated_project.id == project.id
    assert updated_project.name == "Updated Project Name"
    assert updated_project.description == "Updated description"


def test_delete_project(db_engine, sample_project_data):
    """Test deleting a project."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Delete the project
    success = db_service.delete_project(project.id)
    
    # Verify it was deleted
    assert success is True
    # Verify we can't retrieve it anymore
    assert db_service.get_project(project.id) is None


def test_create_task(db_engine, sample_project_data, sample_task_data):
    """Test creating a task associated with a project."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Create a task
    task = db_service.create_task(project.id, sample_task_data)
    
    # Verify it was created with the correct data
    assert isinstance(task, Task)
    assert task.id is not None
    assert task.title == sample_task_data.title
    assert task.description == sample_task_data.description
    assert task.status == sample_task_data.status
    assert task.priority == sample_task_data.priority
    assert task.project_id == project.id
    assert task.meta == sample_task_data.meta  # Updated from task_metadata to meta
    assert task.created_at is not None
    assert task.updated_at is not None


def test_get_task(db_engine, sample_project_data, sample_task_data):
    """Test retrieving a task by ID."""
    # Create a project and task
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    
    # Retrieve the task
    retrieved_task = db_service.get_task(task.id)
    
    # Verify it was retrieved correctly
    assert isinstance(retrieved_task, Task)
    assert retrieved_task.id == task.id
    assert retrieved_task.title == task.title
    assert retrieved_task.description == task.description
    assert retrieved_task.status == task.status


def test_get_tasks_by_project(db_engine, sample_project_data, sample_task_data):
    """Test retrieving all tasks for a project."""
    # Create a project and multiple tasks
    project = db_service.create_project(sample_project_data)
    task1 = db_service.create_task(project.id, sample_task_data)
    task2 = db_service.create_task(
        project.id,
        TaskCreate(
            title="Another Test Task",
            description="Another task for testing",
            status=TaskStatus.TODO
        )
    )
    
    # Retrieve tasks for the project
    tasks = db_service.get_tasks_by_project(project.id)
    
    # Verify we got the right tasks
    assert len(tasks) == 2
    assert all(isinstance(task, Task) for task in tasks)
    assert all(task.project_id == project.id for task in tasks)
    # Verify we have both tasks we created
    task_ids = [task.id for task in tasks]
    assert task1.id in task_ids
    assert task2.id in task_ids


def test_update_task(db_engine, sample_project_data, sample_task_data):
    """Test updating a task."""
    # Create a project and task
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    original_updated_at = task.updated_at
    
    # Update the task
    updated_task = db_service.update_task(
        task.id,
        TaskCreate(
            title="Updated Task Title",
            description="Updated task description",
            status=TaskStatus.IN_PROGRESS
        )
    )
    
    # Verify it was updated
    assert isinstance(updated_task, Task)
    assert updated_task.id == task.id
    assert updated_task.title == "Updated Task Title"
    assert updated_task.description == "Updated task description"
    assert updated_task.status == TaskStatus.IN_PROGRESS
    assert updated_task.updated_at > original_updated_at


def test_delete_task(db_engine, sample_project_data, sample_task_data):
    """Test deleting a task."""
    # Create a project and task
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    
    # Delete the task
    success = db_service.delete_task(task.id)
    
    # Verify it was deleted
    assert success is True
    # Verify we can't retrieve it anymore
    assert db_service.get_task(task.id) is None


def test_create_message(db_engine, sample_project_data, sample_task_data, sample_message_data):
    """Test creating a message associated with a task."""
    # Create a project and task
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    
    # Create a message
    message = db_service.create_message(task.id, sample_message_data)
    
    # Verify it was created with the correct data
    assert isinstance(message, Message)
    assert message.id is not None
    assert message.content == sample_message_data.content
    assert message.role == sample_message_data.role
    assert message.task_id == task.id
    assert message.meta == sample_message_data.meta
    assert message.timestamp is not None


def test_get_message(db_engine, sample_project_data, sample_task_data, sample_message_data):
    """Test retrieving a message by ID."""
    # Create a project, task, and message
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    message = db_service.create_message(task.id, sample_message_data)
    
    # Retrieve the message
    retrieved_message = db_service.get_message(message.id)
    
    # Verify it was retrieved correctly
    assert isinstance(retrieved_message, Message)
    assert retrieved_message.id == message.id
    assert retrieved_message.content == message.content
    assert retrieved_message.role == message.role
    assert retrieved_message.meta == message.meta


def test_get_messages_by_task(db_engine, sample_project_data, sample_task_data, sample_message_data):
    """Test retrieving all messages for a task."""
    # Create a project, task, and multiple messages
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    message1 = db_service.create_message(task.id, sample_message_data)
    message2 = db_service.create_message(
        task.id,
        MessageCreate(
            content="Another test message",
            role=MessageRole.ASSISTANT,
            type="text"
        )
    )
    
    # Retrieve messages for the task
    messages = db_service.get_messages_by_task(task.id)
    
    # Verify we got the right messages
    assert len(messages) == 2
    assert all(isinstance(msg, Message) for msg in messages)
    assert all(msg.task_id == task.id for msg in messages)
    # Verify we have both messages we created
    message_ids = [msg.id for msg in messages]
    assert message1.id in message_ids
    assert message2.id in message_ids


def test_delete_message(db_engine, sample_project_data, sample_task_data, sample_message_data):
    """Test deleting a message."""
    # Create a project, task, and message
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    message = db_service.create_message(task.id, sample_message_data)
    
    # Delete the message
    success = db_service.delete_message(message.id)
    
    # Verify it was deleted
    assert success is True
    # Verify we can't retrieve it anymore
    assert db_service.get_message(message.id) is None


def test_cascading_updates(db_engine, sample_project_data, sample_task_data, sample_message_data):
    """Test that updating a task updates the project's updated_at field."""
    # Create a project and task
    project = db_service.create_project(sample_project_data)
    original_project_updated_at = project.updated_at
    
    # Wait a moment to ensure timestamp difference
    import time
    time.sleep(0.1)
    
    # Create a task
    task = db_service.create_task(project.id, sample_task_data)
    
    # Retrieve the project again
    updated_project = db_service.get_project(project.id)
    
    # Verify the project's updated_at field was updated
    assert updated_project.updated_at > original_project_updated_at


def test_task_completion(db_engine, sample_project_data, sample_task_data):
    """Test that marking a task as completed sets the completed_at field."""
    # Create a project and task
    project = db_service.create_project(sample_project_data)
    task = db_service.create_task(project.id, sample_task_data)
    
    # Verify the task is not completed
    assert task.status == TaskStatus.TODO
    assert task.completed_at is None
    
    # Mark the task as completed
    updated_task = db_service.update_task(
        task.id,
        TaskCreate(
            title=task.title,
            description=task.description,
            status=TaskStatus.COMPLETED
        )
    )
    
    # Verify the task is now completed
    assert updated_task.status == TaskStatus.COMPLETED
    assert updated_task.completed_at is not None


def test_transaction_handling(db_engine, sample_project_data, sample_task_data):
    """Test that transactions work correctly and can be rolled back."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Start a session and transaction for testing
    with Session(db_engine) as session:
        # Begin a transaction
        with session.begin():
            # Create a task in the transaction
            task = Task(
                title="Transaction Test Task",
                description="Testing transaction handling",
                project_id=project.id
            )
            session.add(task)
            
            # Deliberately cause a constraint violation or other error
            # to trigger a rollback
            try:
                # This should fail due to a missing required field or constraint
                invalid_task = Task(title=None)  # Missing required title
                session.add(invalid_task)
                session.flush()  # Force processing to trigger the error
                assert False, "Expected an exception but none was raised"
            except Exception:
                # Expected failure path, transaction should be rolled back
                pass
    
    # Now verify that the first task was NOT saved due to rollback
    with Session(db_engine) as session:
        # Query for tasks with the specified project_id
        tasks = session.exec(
            f"SELECT * FROM task WHERE project_id = '{project.id}'"
        ).all()
        assert len(tasks) == 0, "Task should not exist after rollback"


def test_bulk_operations(db_engine, sample_project_data):
    """Test bulk create/update operations."""
    # Create a project
    project = db_service.create_project(sample_project_data)
    
    # Create multiple tasks in a single transaction
    with Session(db_engine) as session:
        with session.begin():
            tasks = [
                Task(
                    title=f"Bulk Task {i}",
                    description=f"Description for bulk task {i}",
                    project_id=project.id
                )
                for i in range(5)
            ]
            # Add all tasks at once
            for task in tasks:
                session.add(task)
    
    # Verify all tasks were created
    with Session(db_engine) as session:
        db_tasks = session.exec(
            f"SELECT * FROM task WHERE project_id = '{project.id}'"
        ).all()
        assert len(db_tasks) == 5
    
    # Bulk update all tasks
    with Session(db_engine) as session:
        with session.begin():
            # Get all tasks
            tasks = session.exec(
                f"SELECT * FROM task WHERE project_id = '{project.id}'"
            ).all()
            # Update all tasks
            for task in tasks:
                task.status = TaskStatus.IN_PROGRESS
                session.add(task)
    
    # Verify all tasks were updated
    with Session(db_engine) as session:
        updated_tasks = session.exec(
            f"SELECT * FROM task WHERE project_id = '{project.id}' AND status = '{TaskStatus.IN_PROGRESS}'"
        ).all()
        assert len(updated_tasks) == 5 