"""
Database repositories.

This module provides repository classes for working with various models.
Repositories handle the direct database operations.
"""

from typing import List, Optional, Union, Dict, Any
from sqlmodel import Session, select, update
from datetime import datetime
import json

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole, MessageType
)


class BaseRepository:
    """Base repository for common operations."""
    
    def __init__(self, session: Session):
        """Initialize the repository with a database session."""
        self.session = session


class ProjectRepository(BaseRepository):
    """Repository for Project operations."""
    
    def create(self, project_data: Dict[str, Any]) -> Project:
        """Create a new project."""
        project = Project(**project_data)
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project
    
    def get(self, project_id: str) -> Optional[Project]:
        """Get a project by ID."""
        return self.session.exec(
            select(Project).where(Project.id == project_id)
        ).first()
    
    def list(self) -> List[Project]:
        """List all projects."""
        return self.session.exec(select(Project)).all()
    
    def update(self, project_id: str, project_data: Dict[str, Any]) -> Optional[Project]:
        """Update a project."""
        project = self.get(project_id)
        if not project:
            return None
        
        # Update the project
        for key, value in project_data.items():
            setattr(project, key, value)
        
        # Update timestamp
        project.updated_at = datetime.utcnow()
        
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project
    
    def delete(self, project_id: str) -> bool:
        """Delete a project."""
        project = self.get(project_id)
        if not project:
            return False
        
        self.session.delete(project)
        self.session.commit()
        return True


class TaskRepository(BaseRepository):
    """Repository for Task operations."""
    
    def create(self, task_data: Dict[str, Any]) -> Task:
        """Create a new task."""
        task = Task(**task_data)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.session.exec(
            select(Task).where(Task.id == task_id)
        ).first()
    
    def list(self, project_id: Optional[str] = None) -> List[Task]:
        """List tasks, optionally filtered by project."""
        query = select(Task)
        if project_id:
            query = query.where(Task.project_id == project_id)
        return self.session.exec(query).all()
    
    def update(self, task_id: str, task_data: Dict[str, Any]) -> Optional[Task]:
        """Update a task."""
        task = self.get(task_id)
        if not task:
            return None
        
        # Update task fields
        for key, value in task_data.items():
            setattr(task, key, value)
        
        # Update timestamp
        task.updated_at = datetime.utcnow()
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task
    
    def delete(self, task_id: str) -> bool:
        """Delete a task."""
        task = self.get(task_id)
        if not task:
            return False
        
        self.session.delete(task)
        self.session.commit()
        return True
    
    def mark_completed(self, task_id: str) -> Optional[Task]:
        """Mark a task as completed."""
        task = self.get(task_id)
        if not task:
            return None
            
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task


class MessageRepository(BaseRepository):
    """Repository for Message operations."""
    
    def create(self, message_data: Dict[str, Any]) -> Message:
        """Create a new message."""
        message = Message(**message_data)
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message
    
    def get(self, message_id: str) -> Optional[Message]:
        """Get a message by ID."""
        return self.session.exec(
            select(Message).where(Message.id == message_id)
        ).first()
    
    def list_by_task(self, task_id: str) -> List[Message]:
        """List messages for a specific task."""
        return self.session.exec(
            select(Message)
            .where(Message.task_id == task_id)
            .order_by(Message.timestamp)
        ).all()
    
    def list_by_role(self, task_id: str, role: MessageRole) -> List[Message]:
        """List messages by role for a specific task."""
        return self.session.exec(
            select(Message)
            .where(Message.task_id == task_id)
            .where(Message.role == role)
            .order_by(Message.timestamp)
        ).all()
    
    def update(self, message_id: str, message_data: Dict[str, Any]) -> Optional[Message]:
        """Update a message."""
        message = self.get(message_id)
        if not message:
            return None
        
        # Update message fields
        for key, value in message_data.items():
            setattr(message, key, value)
        
        self.session.add(message)
        self.session.commit()
        self.session.refresh(message)
        return message
    
    def delete(self, message_id: str) -> bool:
        """Delete a message."""
        message = self.get(message_id)
        if not message:
            return False
        
        self.session.delete(message)
        self.session.commit()
        return True

# TODO: Implement a proper File model and repository
# class FileRepository(GenericRepository[File]):
#     """Repository for File entities."""
#     
#     def __init__(self, session: Session):
#         super().__init__(session, File)
#     
#     def get_by_task(self, task_id: str) -> List[File]:
#         """
#         Get all files for a task.
#         
#         Args:
#             task_id: ID of the task
#             
#         Returns:
#             List of files for the task
#         """
#         statement = select(File).where(
#             File.task_id == task_id
#         ).order_by(File.created_at)
#         
#         return self.session.exec(statement).all()
#     
#     def get_by_path(self, task_id: str, path: str) -> Optional[File]:
#         """
#         Get a file by its path for a task.
#         
#         Args:
#             task_id: ID of the task
#             path: Path of the file
#             
#         Returns:
#             File if found, None otherwise
#         """
#         statement = select(File).where(
#             File.task_id == task_id,
#             File.path == path
#         )
#         
#         return self.session.exec(statement).first()
#     
#     def get_by_type(self, task_id: str, file_type: str) -> List[File]:
#         """
#         Get all files of a specific type for a task.
#         
#         Args:
#             task_id: ID of the task
#             file_type: Type of the files to get
#             
#         Returns:
#             List of files of the given type
#         """
#         statement = select(File).where(
#             File.task_id == task_id,
#             File.type == file_type
#         ).order_by(File.created_at)
#         
#         return self.session.exec(statement).all() 