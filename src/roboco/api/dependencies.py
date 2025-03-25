"""
API Dependencies

This module provides dependency injection functions for the API endpoints.
These functions are used with FastAPI's dependency injection system.
"""

from typing import Optional

# Remove this import to avoid circular dependency
# from roboco.services.api_service import ApiService
from roboco.services.project_service import ProjectService
from roboco.storage.repositories.file_project_repository import FileProjectRepository

# Singleton instances
_api_service = None


def get_project_service() -> ProjectService:
    """Get the project service instance.
    
    Returns:
        ProjectService instance
    """
    project_repository = FileProjectRepository()
    return ProjectService(project_repository)


def get_api_service():
    """Get the API service instance.
    
    Returns:
        ApiService instance
    """
    # Import here to avoid circular dependency
    from roboco.services.api_service import ApiService
    
    global _api_service
    
    if _api_service is None:
        project_service = get_project_service()
        _api_service = ApiService(project_service)
        
    return _api_service
