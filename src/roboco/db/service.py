"""
Database Service Layer

This module provides service functions for database operations.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, or_
import os
import sqlite3
from loguru import logger

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole, MessageType
)
from roboco.api.models import (
    ProjectCreate, TaskCreate, MessageCreate
)
from roboco.db import get_session, get_session_context
from roboco.utils.id_generator import generate_short_id

# For simplified mock implementation in tests
def create_project(project_data: ProjectCreate):
    """
    Create a new project in the database.
    
    Args:
        project_data: Data for the new project
    """
    # Create project using data from project_data
    project = project_data.to_db_model()
    
    with get_session_context() as session:
        session.add(project)
        session.commit()
        session.refresh(project)
    
    return project


def get_project(project_id: str):
    """
    Get a project by ID.
    
    Args:
        project_id: ID of the project to get
    """
    with get_session_context() as session:
        return session.get(Project, project_id)


def get_all_projects():
    """
    Get all projects.
    """
    with get_session_context() as session:
        return session.exec(select(Project)).all()


def update_project(project_id: str, project_data: ProjectCreate):
    """
    Update a project with new data.
    
    Args:
        project_id: ID of the project to update
        project_data: New data for the project
    """
    with get_session_context() as session:
        project = session.get(Project, project_id)
        
        if not project:
            return None
        
        # Update fields that are present in the update data
        update_data = project_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        
        # Update timestamp
        project.update_timestamp()
        
        session.add(project)
        session.commit()
        session.refresh(project)
        
        return project


def delete_project(project_id: str) -> bool:
    """
    Delete a project by ID.
    
    Args:
        project_id: ID of the project to delete
    """
    with get_session_context() as session:
        project = session.get(Project, project_id)
        
        if not project:
            return False
        
        session.delete(project)
        session.commit()
        
        return True


def create_task(project_id: str, task_data: Any):
    """
    Create a new task in the database.
    
    Args:
        project_id: ID of the project this task belongs to
        task_data: Data for the new task, can be either a TaskCreate or a Task object
    """
    # Create task model from task_data
    if isinstance(task_data, Task):
        task = task_data
    else:
        task = task_data.to_db_model()
    
    # Set project_id
    task.project_id = project_id
    
    with get_session_context() as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Also update the project's updated_at timestamp
        project = session.get(Project, project_id)
        if project:
            project.update_timestamp()
            session.add(project)
            session.commit()
        
        return task


def get_task(task_id: str):
    """
    Get a task by ID.
    
    Args:
        task_id: ID of the task to get
    """
    with get_session_context() as session:
        return session.get(Task, task_id)


def get_tasks_by_project(project_id: str):
    """
    Get all tasks for a project.
    
    Args:
        project_id: ID of the project
    """
    with get_session_context() as session:
        return session.exec(select(Task).where(Task.project_id == project_id)).all()


def update_task(task_id: str, task_data: TaskCreate):
    """
    Update a task with new data.
    
    Args:
        task_id: ID of the task to update
        task_data: New data for the task
    """
    with get_session_context() as session:
        task = session.get(Task, task_id)
        
        if not task:
            return None
        
        # Store the original status to detect status changes
        original_status = task.status
        
        # Update fields from task_data
        update_data = task_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)
        
        # Handle status change to completed
        if task_data.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        # Update timestamp
        task.update_timestamp()
        
        session.add(task)
        session.commit()
        session.refresh(task)
        
        # Also update the project's updated_at timestamp
        project_id = task.project_id
        project = None
        if project_id:
            project = session.get(Project, project_id)
            if project:
                project.update_timestamp()
                session.add(project)
                session.commit()
        
        # If status changed, update the tasks.md file
        status_changed = original_status != task.status
        if status_changed and project_id and project:
            try:
                # Initialize ProjectFS for file access
                from roboco.core.fs import ProjectFS
                fs = ProjectFS(project_id=project_id)
                
                # Check if tasks.md exists
                if fs.exists_sync("tasks.md"):
                    # Create TaskManager instance
                    from roboco.core.task_manager import TaskManager
                    task_manager = TaskManager(fs=fs)
                    
                    # Get all tasks for this project
                    all_tasks = get_tasks_by_project(project_id)
                    
                    # Generate updated markdown
                    markdown_content = task_manager.tasks_to_markdown(all_tasks, project.name)
                    
                    # Write the updated markdown back to tasks.md
                    fs.write_sync("tasks.md", markdown_content)
                    logger.info(f"Updated tasks.md for project {project_id} after task status change")
            except Exception as e:
                # Log but don't fail the operation if tasks.md update fails
                logger.error(f"Failed to update tasks.md after task status change: {str(e)}")
        
        return task


def delete_task(task_id: str) -> bool:
    """
    Delete a task by ID.
    
    Args:
        task_id: ID of the task to delete
    """
    with get_session_context() as session:
        task = session.get(Task, task_id)
        
        if not task:
            return False
        
        # Save project_id before deleting the task
        project_id = task.project_id
        
        session.delete(task)
        session.commit()
        
        # Update the project's updated_at timestamp
        if project_id:
            project = session.get(Project, project_id)
            if project:
                project.update_timestamp()
                session.add(project)
                session.commit()
        
        return True


def create_message(task_id: str, message_data: MessageCreate):
    """
    Create a new message in the database.
    
    Args:
        task_id: ID of the task this message belongs to
        message_data: Data for the new message
    """
    # Create message from message_data
    message = message_data.to_db_model()
    
    # Set task_id
    message.task_id = task_id
    
    with get_session_context() as session:
        session.add(message)
        session.commit()
        session.refresh(message)
        
        # Also update the task's updated_at timestamp
        task = session.get(Task, task_id)
        if task:
            task.update_timestamp()
            session.add(task)
            session.commit()
            
            # Also update the project's updated_at timestamp
            if task.project_id:
                project = session.get(Project, task.project_id)
                if project:
                    project.update_timestamp()
                    session.add(project)
                    session.commit()
        
        return message


def get_message(message_id: str):
    """
    Get a message by ID.
    
    Args:
        message_id: ID of the message to get
    """
    with get_session_context() as session:
        return session.get(Message, message_id)


def get_messages_by_task(task_id: str):
    """
    Get all messages for a task.
    
    Args:
        task_id: ID of the task
    """
    with get_session_context() as session:
        return session.exec(select(Message).where(Message.task_id == task_id)).all()


def delete_message(message_id: str) -> bool:
    """
    Delete a message by ID.
    
    Args:
        message_id: ID of the message to delete
    """
    with get_session_context() as session:
        message = session.get(Message, message_id)
        
        if not message:
            return False
        
        # Save task_id before deleting the message
        task_id = message.task_id
        
        session.delete(message)
        session.commit()
        
        # Update the task's updated_at timestamp
        if task_id:
            task = session.get(Task, task_id)
            if task:
                task.update_timestamp()
                session.add(task)
                session.commit()
                
                # Also update the project's updated_at timestamp
                if task.project_id:
                    project = session.get(Project, task.project_id)
                    if project:
                        project.update_timestamp()
                        session.add(project)
                        session.commit()
        
        return True


def get_last_message_by_project(project_id: str) -> Optional[Message]:
    """Get the last message for a specific project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        The last Message object or None if no messages
    """
    try:
        session = get_session()
        message = session.query(Message).filter(
            Message.project_id == project_id
        ).order_by(Message.created_at.desc()).first()
        return message
    except Exception as e:
        logger.error(f"Error getting last message for project {project_id}: {str(e)}")
        return None 

def create_tasks_batch(tasks_data: List[Dict[str, Any]]) -> List[Task]:
    """
    Create multiple tasks in the database in a single transaction.
    
    Args:
        tasks_data: List of task dictionaries with data for new tasks
        
    Returns:
        List of created Task objects
    """
    created_tasks = []
    
    with get_session_context() as session:
        for task_dict in tasks_data:
            # Create a Task object from the dictionary
            # Make sure required field are present
            if 'title' not in task_dict:
                logger.warning(f"Skipping task without title: {task_dict}")
                continue
                
            # Create task instance
            task = Task(
                id=task_dict.get('id', generate_short_id()),
                title=task_dict['title'],
                description=task_dict.get('description', task_dict['title']),
                status=TaskStatus(task_dict.get('status', 'todo')),
                project_id=task_dict.get('project_id'),
                created_at=datetime.fromisoformat(task_dict['created_at']) if 'created_at' in task_dict else datetime.utcnow(),
                updated_at=datetime.fromisoformat(task_dict['updated_at']) if 'updated_at' in task_dict else datetime.utcnow(),
                completed_at=datetime.fromisoformat(task_dict['completed_at']) if 'completed_at' in task_dict else None,
                meta=task_dict.get('meta', {})
            )
            
            # If details are provided, add them to meta
            if 'details' in task_dict:
                task.meta['details'] = task_dict['details']
            
            session.add(task)
            created_tasks.append(task)
        
        # Update the project's updated_at timestamp if we have tasks with project_id
        project_ids = set(task.project_id for task in created_tasks if task.project_id)
        for project_id in project_ids:
            project = session.get(Project, project_id)
            if project:
                project.update_timestamp()
                session.add(project)
        
        # Commit all changes
        session.commit()
        
        # Refresh all tasks to get their database-assigned values
        for task in created_tasks:
            session.refresh(task)
    
    logger.info(f"Created {len(created_tasks)} tasks in batch")
    return created_tasks 