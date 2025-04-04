"""
Tests for Task database operations.

This module tests the database operations for the Task model.
"""
import pytest
from datetime import datetime

from roboco.core.models import Task, TaskStatus
from roboco.api.models import TaskCreate
from roboco.db import service as db_service
from tests.fixtures.utils import count_rows, get_by_id


class TestTaskDB:
    """Tests for the Task database operations."""

    def test_create_task(self, db_engine, db_session, created_project, sample_task_data):
        """Test creating a task associated with a project."""
        # Create a task
        task = db_service.create_task(created_project.id, sample_task_data)
        
        # Verify it was created with the correct data
        assert isinstance(task, Task)
        assert task.id is not None
        assert task.title == sample_task_data.title
        assert task.description == sample_task_data.description
        assert task.status == sample_task_data.status
        assert task.priority == sample_task_data.priority
        assert task.project_id == created_project.id
        assert task.meta == sample_task_data.meta
        assert task.created_at is not None
        assert task.updated_at is not None
        
        # Verify it exists in the database
        db_task = get_by_id(db_session, Task, task.id)
        assert db_task is not None
        assert db_task.title == sample_task_data.title

    def test_get_task(self, db_engine, db_session, created_task):
        """Test retrieving a task by ID."""
        # Retrieve the task
        retrieved_task = db_service.get_task(created_task.id)
        
        # Verify it was retrieved correctly
        assert isinstance(retrieved_task, Task)
        assert retrieved_task.id == created_task.id
        assert retrieved_task.title == created_task.title
        assert retrieved_task.description == created_task.description
        assert retrieved_task.status == created_task.status

    def test_get_tasks_by_project(self, db_engine, db_session, created_project, sample_task_data):
        """Test retrieving all tasks for a project."""
        # Create multiple tasks
        task1 = db_service.create_task(created_project.id, sample_task_data)
        task2 = db_service.create_task(
            created_project.id,
            TaskCreate(
                title="Another Test Task",
                description="Another task for testing",
                status=TaskStatus.TODO
            )
        )
        
        # Retrieve tasks for the project
        tasks = db_service.get_tasks_by_project(created_project.id)
        
        # Verify we got the right tasks
        assert len(tasks) == 2
        assert all(isinstance(task, Task) for task in tasks)
        assert all(task.project_id == created_project.id for task in tasks)
        
        # Verify both tasks are in the result
        task_ids = [task.id for task in tasks]
        assert task1.id in task_ids
        assert task2.id in task_ids

    def test_update_task(self, db_engine, db_session, created_task):
        """Test updating a task."""
        original_updated_at = created_task.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Update the task
        updated_task = db_service.update_task(
            created_task.id,
            TaskCreate(
                title="Updated Task Title",
                description="Updated task description",
                status=TaskStatus.IN_PROGRESS
            )
        )
        
        # Verify it was updated
        assert isinstance(updated_task, Task)
        assert updated_task.id == created_task.id
        assert updated_task.title == "Updated Task Title"
        assert updated_task.description == "Updated task description"
        assert updated_task.status == TaskStatus.IN_PROGRESS
        assert updated_task.updated_at > original_updated_at
        
        # Verify the update persisted in the database
        db_task = get_by_id(db_session, Task, created_task.id)
        assert db_task.title == "Updated Task Title"
        assert db_task.status == TaskStatus.IN_PROGRESS

    def test_delete_task(self, db_engine, db_session, created_task):
        """Test deleting a task."""
        # Delete the task
        success = db_service.delete_task(created_task.id)
        
        # Verify it was deleted
        assert success is True
        
        # Verify we can't retrieve it anymore
        assert db_service.get_task(created_task.id) is None
        assert get_by_id(db_session, Task, created_task.id) is None

    def test_task_completion(self, db_engine, db_session, created_task):
        """Test that marking a task as completed sets the completed_at field."""
        # Verify the task is not completed initially
        assert created_task.status == TaskStatus.TODO
        assert created_task.completed_at is None
        
        # Mark the task as completed
        updated_task = db_service.update_task(
            created_task.id,
            TaskCreate(
                title=created_task.title,
                description=created_task.description,
                status=TaskStatus.COMPLETED
            )
        )
        
        # Verify the task is now completed
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.completed_at is not None
        
        # Verify the update persisted in the database
        db_task = get_by_id(db_session, Task, created_task.id)
        assert db_task.status == TaskStatus.COMPLETED
        assert db_task.completed_at is not None 