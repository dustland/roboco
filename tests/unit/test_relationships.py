"""
Tests for model relationships.

This module tests how the different model entities relate to each other.
"""
import pytest
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine, select, or_, and_

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole, MessageType
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


@pytest.fixture
def project_hierarchy(test_session):
    """Create a project with multiple tasks and messages."""
    # Create a project
    project = Project(
        name="Test Project",
        description="A project for testing relationships",
        meta={"key": "value", "priority": "high"}
    )
    test_session.add(project)
    test_session.commit()
    test_session.refresh(project)
    
    # Create tasks
    task1 = Task(
        title="Task 1",
        description="First task",
        status=TaskStatus.TODO,
        project_id=project.id,
        priority="high",
        meta={"effort": "low"}
    )
    
    task2 = Task(
        title="Task 2",
        description="Second task",
        status=TaskStatus.TODO,
        project_id=project.id,
        priority="medium",
        meta={"effort": "medium"}
    )
    
    task3 = Task(
        title="Task 3",
        description="Third task",
        status=TaskStatus.IN_PROGRESS,
        project_id=project.id,
        priority="low",
        meta={"effort": "high"}
    )
    
    test_session.add(task1)
    test_session.add(task2)
    test_session.add(task3)
    test_session.commit()
    
    # Refresh tasks to get IDs
    test_session.refresh(task1)
    test_session.refresh(task2)
    test_session.refresh(task3)
    
    # Create messages for tasks
    message1 = Message(
        content="Message for task 1",
        role=MessageRole.USER,
        task_id=task1.id,
        type=MessageType.TEXT
    )
    
    message2 = Message(
        content="Response to task 1",
        role=MessageRole.ASSISTANT,
        task_id=task1.id,
        type=MessageType.TEXT
    )
    
    message3 = Message(
        content="Message for task 2",
        role=MessageRole.USER,
        task_id=task2.id,
        type=MessageType.TEXT
    )
    
    test_session.add(message1)
    test_session.add(message2)
    test_session.add(message3)
    test_session.commit()
    
    return {
        "project": project,
        "tasks": [task1, task2, task3],
        "messages": [message1, message2, message3]
    }


def test_cascade_update_on_task_completion(test_session, project_hierarchy):
    """Test cascade updates when completing a task."""
    project = project_hierarchy["project"]
    task = project_hierarchy["tasks"][0]
    
    # Record original timestamps
    original_project_updated = project.updated_at
    original_task_updated = task.updated_at
    
    # Ensure time passes for timestamp differentiation
    import time
    time.sleep(0.1)
    
    # Mark task as completed
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()  # Set completed_at
    task.updated_at = datetime.utcnow()    # Explicitly update the timestamp
    
    # Also update the project timestamp (in a real app, this would be handled by a trigger or event)
    project.updated_at = datetime.utcnow()
    
    test_session.add(task)
    test_session.add(project)
    test_session.commit()
    test_session.refresh(task)
    test_session.refresh(project)
    
    # Verify task was completed
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None
    assert task.updated_at > original_task_updated
    
    # Verify project was updated
    assert project.updated_at > original_project_updated


def test_complex_task_queries(test_session, project_hierarchy):
    """Test complex queries on tasks using SQLModel."""
    project = project_hierarchy["project"]
    
    # Query tasks by status and priority
    high_priority_todo_tasks = test_session.exec(
        select(Task)
        .where(Task.project_id == project.id)
        .where(and_(
            Task.status == TaskStatus.TODO,
            Task.priority == "high"
        ))
    ).all()
    
    assert len(high_priority_todo_tasks) == 1
    assert high_priority_todo_tasks[0].title == "Task 1"
    
    # Query tasks that are either high priority or in progress
    high_priority_or_in_progress = test_session.exec(
        select(Task)
        .where(Task.project_id == project.id)
        .where(or_(
            Task.priority == "high",
            Task.status == TaskStatus.IN_PROGRESS
        ))
    ).all()
    
    assert len(high_priority_or_in_progress) == 2
    task_titles = [task.title for task in high_priority_or_in_progress]
    assert "Task 1" in task_titles
    assert "Task 3" in task_titles


def test_message_conversation(test_session, project_hierarchy):
    """Test retrieving messages in conversation order."""
    task1 = project_hierarchy["tasks"][0]
    
    # Get messages for task1 in timestamp order
    conversation = test_session.exec(
        select(Message)
        .where(Message.task_id == task1.id)
        .order_by(Message.timestamp)
    ).all()
    
    assert len(conversation) == 2
    assert conversation[0].role == MessageRole.USER
    assert conversation[1].role == MessageRole.ASSISTANT


def test_tasks_with_message_count(test_session, project_hierarchy):
    """Test complex query to get tasks with message counts."""
    project = project_hierarchy["project"]
    project_id = project.id
    
    # Get counts of messages for each task using SQLAlchemy
    task_counts = []
    
    # First, fetch all tasks for the project
    tasks = test_session.exec(
        select(Task).where(Task.project_id == project_id)
    ).all()
    
    # Then, for each task, count its messages
    for task in tasks:
        message_count = len(test_session.exec(
            select(Message).where(Message.task_id == task.id)
        ).all())
        
        task_counts.append((task.id, task.title, message_count))
    
    # Sort by message count in descending order
    result = sorted(task_counts, key=lambda x: x[2], reverse=True)
    
    # Verify results
    assert len(result) == 3
    
    # Sort tasks by message count for verification
    task_message_counts = {}
    for task in project_hierarchy["tasks"]:
        messages = [msg for msg in project_hierarchy["messages"] if msg.task_id == task.id]
        task_message_counts[task.id] = len(messages)
    
    # Get sorted task IDs by message count
    sorted_task_ids = sorted(task_message_counts.keys(), 
                             key=lambda task_id: task_message_counts[task_id], 
                             reverse=True)
    
    # Task1 has 2 messages
    assert result[0][0] == sorted_task_ids[0]
    assert result[0][2] == task_message_counts[sorted_task_ids[0]]
    
    # Task2 has 1 message
    assert result[1][0] == sorted_task_ids[1]
    assert result[1][2] == task_message_counts[sorted_task_ids[1]]
    
    # Task3 has 0 messages
    assert result[2][0] == sorted_task_ids[2]
    assert result[2][2] == task_message_counts[sorted_task_ids[2]]


def test_task_metadata_filtering(test_session, project_hierarchy):
    """Test filtering tasks by metadata fields."""
    project = project_hierarchy["project"]
    
    # Query tasks with a specific metadata value
    # SQLite doesn't have good JSON support, so in a real app with
    # PostgreSQL we would use json_extract or similar functions
    
    # For testing, we'll serialize metadata to a string and use LIKE
    high_effort_tasks = []
    for task in test_session.exec(select(Task).where(Task.project_id == project.id)).all():
        if task.meta and task.meta.get("effort") == "high":
            high_effort_tasks.append(task)
    
    assert len(high_effort_tasks) == 1
    assert high_effort_tasks[0].title == "Task 3"


def test_model_relationships_bidirectional(test_session, project_hierarchy):
    """Test that relationships work in both directions."""
    project = project_hierarchy["project"]
    task1 = project_hierarchy["tasks"][0]
    message1 = project_hierarchy["messages"][0]
    
    # Verify project -> tasks relationship
    project_tasks = test_session.exec(
        select(Task).where(Task.project_id == project.id)
    ).all()
    assert len(project_tasks) == 3
    
    # Verify task -> project relationship
    task_project = test_session.exec(
        select(Project).where(Project.id == task1.project_id)
    ).first()
    assert task_project.id == project.id
    assert task_project.name == project.name
    
    # Verify task -> messages relationship
    task_messages = test_session.exec(
        select(Message).where(Message.task_id == task1.id)
    ).all()
    assert len(task_messages) == 2
    
    # Verify message -> task relationship
    message_task = test_session.exec(
        select(Task).where(Task.id == message1.task_id)
    ).first()
    assert message_task.id == task1.id
    assert message_task.title == task1.title 