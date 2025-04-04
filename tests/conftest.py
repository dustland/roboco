"""
Global test fixtures and configuration.

This module ensures the base fixtures are loaded before any tests run.
"""
import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text

from roboco.core.models import (
    Project, Task, Message,
    TaskStatus, MessageRole, MessageType
)

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
    """Create a test engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def test_session(test_engine):
    """Create a test session."""
    with Session(test_engine) as session:
        yield session
        session.rollback()


# Database test fixtures (equivalent to test_engine and test_session)
@pytest.fixture(scope="session")
def db_engine():
    """Create a database engine for tests."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a database session for tests."""
    with Session(db_engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def clean_db(db_session):
    """Clean database before test."""
    tables = ["messages", "tasks", "projects"]
    for table in tables:
        db_session.execute(text(f"DELETE FROM {table}"))
    db_session.commit()
    return db_session 