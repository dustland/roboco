"""
Database module for Roboco.

This module provides the database configuration and access layer.
"""

import os
from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

# Get database URL from environment or use SQLite default
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./roboco.db")

# Create engine
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)


def create_db_and_tables():
    """Create all database tables if they don't exist."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: The database session
    """
    return Session(engine)


@contextmanager
def get_session_context() -> Iterator[Session]:
    """
    Create a session context manager.
    
    This ensures the session is properly closed after use, even if an exception occurs.
    
    Example:
        >>> with get_session_context() as session:
        >>>     # Use session here
    
    Yields:
        Session: The database session
    """
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_or_create(session: Session, model, **kwargs):
    """Get an existing object or create a new one."""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    
    instance = model(**kwargs)
    session.add(instance)
    session.flush()
    return instance, True 

# Initialize database
def init_db():
    """Initialize the database by creating all tables."""
    SQLModel.metadata.create_all(engine)

# Create tables on module import
init_db()

__all__ = [
    'get_session',
    'get_session_context',
    'init_db'
] 