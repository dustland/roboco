"""
Project Service

This module provides services for managing projects, including project creation
and retrieval of project status.
"""

from typing import List, Optional, Dict, Any, Union
from pathlib import Path
import os
from datetime import datetime
import json

from roboco.core.config import load_config, get_workspace
from loguru import logger
from roboco.core.project_manager import ProjectManager
from roboco.core.fs import ProjectFS, ProjectNotFoundError, get_project_fs
from roboco.teams.planning import PlanningTeam
from roboco.utils.id_generator import generate_short_id

logger = logger.bind(module=__name__)


class ProjectService:
    """
    Service for managing projects.
    
    This service provides methods for creating projects and retrieving project status.
    Since tasks are AI-generated and not meant to be manually edited, update operations
    are intentionally limited.
    """

    def __init__(self):
        """Initialize the project service."""
        self.config = load_config()
        self.workspace_dir = str(get_workspace(self.config))

    async def get_project(self, project_id: str) -> Optional[ProjectManager]:
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            ProjectManager instance or None if not found
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import get_project
        
        # Get project from database
        project_data = get_project(project_id)
        
        if not project_data:
            return None
            
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Create and return project manager
        return ProjectManager(
            project=project_data,
            fs=fs
        )

    async def list_projects(self) -> List[ProjectManager]:
        """
        List all projects.
        
        Returns:
            List of ProjectManager instances
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import get_all_projects
        
        # Get all projects from database
        project_data_list = get_all_projects()
        
        # Create ProjectManager instances for each project
        project_managers = []
        for project_data in project_data_list:
            fs = ProjectFS(project_id=project_data.id)
            project_manager = ProjectManager(
                project=project_data,
                fs=fs
            )
            project_managers.append(project_manager)
            
        return project_managers

    async def create_project(
        self, 
        name: str,
        description: str = "",
        project_id: Optional[str] = None,
    ) -> ProjectManager:
        """
        Create a new project.
        
        Args:
            name: Name of the project
            description: Optional description of the project
            project_id: Optional specific ID to use
            
        Returns:
            ProjectManager instance for the new project
        """
        # Use provided ID or generate a new one
        project_id = project_id or generate_short_id()
        
        # Import DB operations here to avoid circular imports
        from roboco.db.service import create_project
        
        # Create Project instance
        project = Project(
            id=project_id,
            name=name,
            description=description,
        )
        
        # Save to database
        from roboco.db import get_session_context
        with get_session_context() as session:
            session.add(project)
            session.commit()
            session.refresh(project)
        
        # Create filesystem for the project
        fs = ProjectFS(project_id=project_id)
        
        # Create standard directory structure
        fs.mkdir_sync("src")
        fs.mkdir_sync("docs")
        
        # Create and return project manager
        return ProjectManager(
            project=project,
            fs=fs
        )

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get the status of a project including task completion status from database.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dictionary with project status information.
            
        Raises:
            ProjectNotFoundError: If the project cannot be found.
        """
        # Import DB operations here to avoid circular imports
        from roboco.db.service import get_project, get_tasks_by_project
        
        # Get project from database
        project = get_project(project_id)
        if not project:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found in database")
        
        # Get tasks from database
        tasks = get_tasks_by_project(project_id)
        
        # Count completed vs total tasks
        completed_tasks = sum(1 for task in tasks if task.status == "completed" or task.status == "COMPLETED")
        total_tasks = len(tasks)
        
        # Calculate progress percentage (avoid division by zero)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Create ProjectFS instance to get the path
        project_fs = ProjectFS(project_id=project_id)
        
        # Return comprehensive status information
        return {
            "id": project_id,
            "name": project.name,
            "description": project.description,
            "status": "completed" if completed_tasks == total_tasks and total_tasks > 0 else "in_progress",
            "progress": round(progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "created_at": project.created_at.isoformat() if project.created_at else datetime.now().isoformat(),
            "updated_at": project.updated_at.isoformat() if project.updated_at else datetime.now().isoformat(),
            "project_id": project_id,
            "path": str(project_fs.base_dir)
        }

    async def initiate_project(
        self, 
        query: str, 
        teams: Optional[List[str]] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> ProjectManager:
        """
        Initiate a new project based on a natural language query.
        
        Uses PlanningTeam to intelligently parse the query and create a project
        with appropriate attributes and structure.
        
        Args:
            query: Natural language description of the project
            teams: List of teams to assign to the project
            metadata: Optional metadata to store with the project
            project_id: Optional pre-generated project ID to use consistently
            
        Returns:
            The created project with all details
        """
        # Use provided ID or generate a new one
        project_id = project_id or generate_short_id()
        logger.info(f"Initiating project from query: {query} with ID: {project_id}")
        
        # Create planning team and run planning
        planning_team = PlanningTeam(project_id=project_id)
        
        # Prepare context with metadata to pass to planning phase
        context = {"project_id": project_id, "query": query}
        # If metadata is provided, include it in the context for the planning phase
        if metadata:
            context["metadata"] = metadata
        
        # Run the planning process with the enhanced context
        planning_result = await planning_team.run_chat(
            query=query,
            teams=teams or ["planning"],
            context=context
        )
        
        # Get the project instance directly from the planning result
        project = planning_result.get("project")
        
        # Verify we have a valid project
        if not project:
            raise ValueError(f"Planning phase did not create a valid project for ID {project_id}")
        
        return project

    async def execute_project(self, project_or_id: Union[str, 'ProjectManager']) -> Dict[str, Any]:
        """
        Execute the project by running its defined tasks.
        
        Args:
            project_or_id: Either a ProjectManager instance or a project ID string
            
        Returns:
            Dictionary with execution results
        """
        # Handle both ProjectManager instance and project_id string
        if isinstance(project_or_id, str):
            # Load the project manager if a string ID was provided
            project = ProjectManager.load(project_or_id)
        else:
            # Use the provided ProjectManager instance directly
            project = project_or_id
            
        # Execute tasks
        results = await project.execute_tasks()
        
        return results 