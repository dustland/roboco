"""
Tests for Project database operations.

This module tests the database operations for the Project model.
"""
import pytest
from datetime import datetime
from sqlalchemy import text
from sqlmodel import select

from roboco.core.models import Project
from roboco.api.models import ProjectCreate, ProjectUpdate
from tests.fixtures.utils import count_rows, get_by_id


class TestProjectDB:
    """Tests for the Project database operations."""

    def test_create_project(self, db_session, clean_db, sample_project_data):
        """Test creating a project."""
        # Get initial count
        initial_count = count_rows(db_session, "projects")
        assert initial_count == 0
        
        # Create a project directly in the session
        project_data = sample_project_data.model_dump()
        project = Project(**project_data)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        # Verify it was created with the correct data
        assert isinstance(project, Project)
        assert project.id is not None
        assert project.name == sample_project_data.name
        assert project.description == sample_project_data.description
        assert project.meta == sample_project_data.meta
        assert project.created_at is not None
        assert project.updated_at is not None
        
        # Get fresh data from the session
        db_session.expire_all()
        db_project = get_by_id(db_session, Project, project.id)
        assert db_project is not None
        assert db_project.name == sample_project_data.name

    def test_get_project(self, db_session, clean_db, sample_project_data):
        """Test retrieving a project by ID."""
        # Create a project first
        project_data = sample_project_data.model_dump()
        project = Project(**project_data)
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        # Retrieve the project using a direct query
        retrieved_project = get_by_id(db_session, Project, project.id)
        
        # Verify it was retrieved correctly
        assert isinstance(retrieved_project, Project)
        assert retrieved_project.id == project.id
        assert retrieved_project.name == project.name
        assert retrieved_project.description == project.description

    def test_list_projects(self, db_session, clean_db, sample_project_data):
        """Test retrieving all projects."""
        # Create multiple projects
        project1 = Project(**sample_project_data.model_dump())
        db_session.add(project1)
        
        project2 = Project(
            name="Test Project 2",
            description="Another project for testing"
        )
        db_session.add(project2)
        db_session.commit()
        db_session.refresh(project1)
        db_session.refresh(project2)
        
        # Get the count
        count = count_rows(db_session, "projects")
        assert count == 2
        
        # Retrieve all projects
        projects = db_session.exec(select(Project)).all()
        
        # Verify all projects were retrieved
        assert len(projects) == 2
        assert any(p.id == project1.id for p in projects)
        assert any(p.id == project2.id for p in projects)
        assert all(isinstance(project, Project) for project in projects)

    def test_update_project(self, db_session, clean_db, sample_project_data):
        """Test updating a project."""
        # Create a project first
        project = Project(**sample_project_data.model_dump())
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        original_updated_at = project.updated_at
        
        # Wait a moment to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        # Update the project
        project.name = "Updated Project Name"
        project.description = "Updated description"
        project.updated_at = datetime.utcnow()
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        # Verify it was updated
        assert isinstance(project, Project)
        assert project.name == "Updated Project Name"
        assert project.description == "Updated description"
        assert project.updated_at > original_updated_at
        
        # Verify the update persisted in the database
        db_session.expire_all()
        db_project = get_by_id(db_session, Project, project.id)
        assert db_project.name == "Updated Project Name"

    def test_delete_project(self, db_session, clean_db, sample_project_data):
        """Test deleting a project."""
        # Create a project first
        project = Project(**sample_project_data.model_dump())
        db_session.add(project)
        db_session.commit()
        db_session.refresh(project)
        
        # Get the project ID before deleting
        project_id = project.id
        
        # Delete the project
        db_session.delete(project)
        db_session.commit()
        
        # Verify we can't retrieve it anymore
        db_session.expire_all()
        db_project = get_by_id(db_session, Project, project_id)
        assert db_project is None 