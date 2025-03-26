"""
Project Service

This module provides services for managing projects, including project creation
and retrieval of project status.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import os
from datetime import datetime

from roboco.core.config import load_config, get_workspace
from roboco.core.logger import get_logger
from roboco.core.models import Project
from roboco.core.project_fs import ProjectFS, ProjectNotFoundError, get_project_fs

logger = get_logger(__name__)


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

    async def get_project(self, project_id: str) -> Project:
        """
        Retrieve a project by its ID.
        
        Args:
            project_id: The ID of the project to retrieve.
            
        Returns:
            The Project with the specified ID.
            
        Raises:
            ProjectNotFoundError: If the project cannot be found.
        """
        project_fs = await ProjectFS.get_by_id(project_id)
        return await project_fs.get_project()

    async def list_projects(self) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all projects.
        """
        return await ProjectFS.list_all()

    async def create_project(
        self,
        name: str,
        description: str,
        directory: Optional[str] = None,
        teams: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Name of the project.
            description: Description of the project.
            directory: Custom directory name (optional).
            teams: Teams involved in the project (optional).
            tags: Tags for the project (optional).
            
        Returns:
            The newly created Project.
        """
        project_fs = await ProjectFS.create(
            name=name,
            description=description,
            directory=directory,
            teams=teams or [],
            tags=tags or []
        )
        
        return await project_fs.get_project()

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get the status of a project including task completion status.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            Dictionary with project status information.
            
        Raises:
            ProjectNotFoundError: If the project cannot be found.
        """
        # Get the project
        project_fs = await ProjectFS.get_by_id(project_id)
        project = await project_fs.get_project()
        
        # Get task information from tasks.md
        tasks_file_path = Path(project_fs.path) / "tasks.md"
        tasks_content = ""
        
        if tasks_file_path.exists():
            with open(tasks_file_path, "r", encoding="utf-8") as f:
                tasks_content = f.read()
        
        # Count completed vs total tasks
        completed_tasks = 0
        total_tasks = 0
        
        for line in tasks_content.splitlines():
            line = line.strip()
            if line.startswith("- ["):
                total_tasks += 1
                if line.startswith("- [x]"):
                    completed_tasks += 1
        
        # Calculate progress percentage (avoid division by zero)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Return comprehensive status information
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": "completed" if completed_tasks == total_tasks and total_tasks > 0 else "in_progress",
            "progress": round(progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "directory": project.directory,
            "path": str(project_fs.path)
        }

    async def find_projects_by_name(self, name: str) -> List[Project]:
        """
        Find projects by name.
        
        Args:
            name: Name to search for (case-insensitive partial match).
            
        Returns:
            List of projects matching the name.
        """
        return await ProjectFS.find_by_name(name)

    async def get_project_directory(self, project_id: str) -> Optional[str]:
        """
        Get the directory name for a project by its ID.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The directory name of the project, or None if not found.
        """
        try:
            project_fs = await ProjectFS.get_by_id(project_id)
            
            # Prioritize path attribute
            if hasattr(project_fs, 'path'):
                return os.path.basename(str(project_fs.path))
            
            # Fall back to base_dir if path not available
            if hasattr(project_fs, 'base_dir'):
                return os.path.basename(str(project_fs.base_dir))
            
            # Last resort: get project and use directory attribute
            project = await project_fs.get_project()
            return project.directory if project.directory else None
        except Exception:
            # Return None if project not found
            return None

    async def create_project_from_query(
        self, 
        query: str, 
        teams: Optional[List[str]] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a project from a natural language query.
        
        Uses PlanningTeam to intelligently parse the query and create a project
        with appropriate attributes and structure.
        
        Args:
            query: Natural language description of the project
            teams: List of teams to assign to the project
            metadata: Optional metadata to store with the project
            
        Returns:
            The created project with all details
        """
        from roboco.teams.planning import PlanningTeam
        
        # Log the start of project creation
        logger.info(f"Creating project from query: {query}")
        
        # Create planning team with workspace directory
        planning_team = PlanningTeam()
        
        # Get planning result - let exceptions propagate
        planning_result = await planning_team.run_chat(
            query=query,
            teams=teams
        )
        
        # Get project directory directly from planning result
        directory_name = planning_result.get("project_dir")
        
        if not directory_name:
            raise ValueError("Could not get project directory from planning result")
        
        # Create the full project path
        project_dir = os.path.join(self.workspace_dir, directory_name)
        
        # Create ProjectFS instance
        project_fs = ProjectFS(project_dir=project_dir)
                
        # Get project and add metadata
        project = await project_fs.get_project()
        
        # Add metadata if provided
        if metadata:
            project.metadata.update(metadata)
        
        project.metadata["summary"] = planning_result.get("summary", "")
        project.metadata["created_at"] = datetime.now().isoformat()
        
        # Save updates
        await project_fs.save_project(project)
        
        return project
    