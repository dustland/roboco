"""
Test utilities for testing.

This module provides helper functions and utilities for testing.
"""
from sqlmodel import Session, SQLModel, select
from sqlalchemy import text
from typing import List, Dict, Any, Optional, Type

from roboco.core.models import Project, Task, Message


def clear_tables(session: Session) -> None:
    """Clear all tables in the database."""
    # Clear messages first (foreign key constraint)
    session.execute(text("DELETE FROM messages"))
    # Clear tasks
    session.execute(text("DELETE FROM tasks"))
    # Clear projects
    session.execute(text("DELETE FROM projects"))
    session.commit()


def count_rows(session: Session, table_name: str) -> int:
    """
    Count rows in a table.
    
    Args:
        session: SQLModel session
        table_name: Name of the table to count
        
    Returns:
        Number of rows in the table
    """
    result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
    return result.scalar()


def get_all_from_table(session: Session, table_name: str) -> List[Dict[str, Any]]:
    """Get all rows from a table as dictionaries."""
    result = session.execute(text(f"SELECT * FROM {table_name}"))
    return [dict(row._mapping) for row in result]


def get_by_id(session: Session, model_class: Type[SQLModel], id_value: str) -> Optional[SQLModel]:
    """
    Get a model instance by ID.
    
    Args:
        session: SQLModel session
        model_class: SQLModel class to query
        id_value: ID value to search for
        
    Returns:
        Model instance if found, None otherwise
    """
    return session.exec(
        select(model_class).where(model_class.id == id_value)
    ).first()


def verify_model_data(model_instance: Any, expected_data: Dict[str, Any]) -> None:
    """Verify that a model instance has the expected data."""
    for key, value in expected_data.items():
        assert hasattr(model_instance, key), f"Model does not have attribute {key}"
        assert getattr(model_instance, key) == value, f"Expected {key}={value}, got {getattr(model_instance, key)}"


def truncate_tables(session: Session, table_names: list[str]) -> None:
    """
    Truncate multiple tables.
    
    Args:
        session: SQLModel session
        table_names: List of table names to truncate
    """
    for table in table_names:
        session.execute(text(f"DELETE FROM {table}"))
    session.commit() 