"""
Tests for advanced database operations.

This module tests more complex database operations like transactions,
cascading updates, and bulk operations.
"""
import pytest
from datetime import datetime
from sqlmodel import Session, text

from roboco.core.models import Project, Task, Message, TaskStatus
from roboco.api.models import ProjectCreate, TaskCreate, MessageCreate
from roboco.db import service as db_service
from tests.fixtures.utils import count_rows, get_by_id, clear_tables


class TestAdvancedDBOperations:
    """Tests for advanced database operations."""

    def test_cascading_updates(self, db_engine, db_session, created_project, created_task):
        """Test that updating a child entity updates parent timestamps."""
        # Record original timestamps
        project_original_updated_at = created_project.updated_at
        task_original_updated_at = created_task.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Create a message (which should update both task and project timestamps)
        message = db_service.create_message(
            created_task.id,
            MessageCreate(
                content="Test message for cascading updates",
                task_id=created_task.id
            )
        )
        
        # Refresh project and task from database
        refreshed_project = db_service.get_project(created_project.id)
        refreshed_task = db_service.get_task(created_task.id)
        
        # Verify timestamps were updated
        assert refreshed_task.updated_at > task_original_updated_at
        assert refreshed_project.updated_at > project_original_updated_at
        
    def test_transaction_with_session(self, db_engine, created_project):
        """Test that transactions work correctly within a session."""
        # Get the initial task count
        with Session(db_engine) as session:
            initial_task_count = session.exec(
                text(f"SELECT COUNT(*) FROM tasks WHERE project_id = :project_id"),
                {"project_id": created_project.id}
            ).one()[0]
        
        # Try a transaction that should succeed
        with Session(db_engine) as session:
            with session.begin():
                task = Task(
                    title="Transaction Success Task",
                    description="This task should be saved",
                    project_id=created_project.id,
                    status=TaskStatus.TODO
                )
                session.add(task)
        
        # Verify the task was saved
        with Session(db_engine) as session:
            new_task_count = session.exec(
                text(f"SELECT COUNT(*) FROM tasks WHERE project_id = :project_id"),
                {"project_id": created_project.id}
            ).one()[0]
            assert new_task_count == initial_task_count + 1
        
        # Try a transaction that should fail
        try:
            with Session(db_engine) as session:
                with session.begin():
                    task = Task(
                        title="Transaction Failure Task",
                        description="This task should not be saved",
                        project_id=created_project.id,
                        status=TaskStatus.TODO
                    )
                    session.add(task)
                    
                    # Add a task with an invalid status to force a rollback
                    invalid_task = Task(
                        title="Invalid Task",
                        description="This has an invalid status",
                        project_id=created_project.id,
                        status="INVALID_STATUS"  # This will cause an error
                    )
                    session.add(invalid_task)
        except Exception:
            # Expected exception
            pass
            
        # Verify no new tasks were saved from the failed transaction
        with Session(db_engine) as session:
            final_task_count = session.exec(
                text(f"SELECT COUNT(*) FROM tasks WHERE project_id = :project_id"),
                {"project_id": created_project.id}
            ).one()[0]
            assert final_task_count == initial_task_count + 1  # Only the first task was saved
            
            # Verify the "Transaction Failure Task" does not exist
            task_titles = session.exec(
                text(f"SELECT title FROM tasks WHERE project_id = :project_id"),
                {"project_id": created_project.id}
            ).all()
            assert "Transaction Failure Task" not in [t[0] for t in task_titles]
        
    def test_bulk_operations(self, db_engine, db_session, created_project):
        """Test bulk create and update operations."""
        # Clear existing tasks
        tasks_before = db_session.exec(
            text(f"SELECT COUNT(*) FROM tasks WHERE project_id = :project_id"),
            {"project_id": created_project.id}
        ).one()[0]
        
        # Bulk create 5 tasks
        tasks_to_create = []
        for i in range(5):
            with Session(db_engine) as session:
                task = Task(
                    title=f"Bulk Task {i}",
                    description=f"Description for bulk task {i}",
                    project_id=created_project.id,
                    status=TaskStatus.TODO
                )
                session.add(task)
                session.commit()
                tasks_to_create.append(task.id)
                
        # Verify all tasks were created
        with Session(db_engine) as session:
            tasks_after = session.exec(
                text(f"SELECT COUNT(*) FROM tasks WHERE project_id = :project_id"),
                {"project_id": created_project.id}
            ).one()[0]
            assert tasks_after == tasks_before + 5
        
        # Bulk update all tasks to IN_PROGRESS
        for task_id in tasks_to_create:
            db_service.update_task(
                task_id,
                TaskCreate(
                    title=f"Updated Task {task_id}",
                    status=TaskStatus.IN_PROGRESS
                )
            )
        
        # Verify all tasks were updated
        with Session(db_engine) as session:
            in_progress_count = session.exec(
                text(f"SELECT COUNT(*) FROM tasks WHERE project_id = :project_id AND status = :status"),
                {"project_id": created_project.id, "status": TaskStatus.IN_PROGRESS}
            ).one()[0]
            assert in_progress_count >= 5  # At least our 5 tasks should be IN_PROGRESS 