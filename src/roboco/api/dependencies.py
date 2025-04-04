"""
API Dependencies

This module contains FastAPI dependencies used across multiple routers.
Moving these to a separate module helps prevent circular imports.
"""

from roboco.core.models import Project, Task
from roboco.services.project_service import ProjectService
from roboco.services.agent_service import AgentService


def get_api_service():
    """
    Get a dependency-injected instance of the API service.
    
    This function is used by FastAPI's dependency injection system to
    provide a consistent instance of the API service to the routers.
    
    Returns:
        The API service instance
    """
    from roboco.services import ApiService
    return ApiService.get_instance()
