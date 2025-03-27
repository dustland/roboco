"""
Project Service

This module provides services for managing projects, including project creation
and retrieval of project status.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import os
from datetime import datetime
import json
from uuid import uuid4

from roboco.core.config import load_config, get_workspace
from loguru import logger
from roboco.core.models import Project
from roboco.core.project_fs import ProjectFS, ProjectNotFoundError, get_project_fs
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
        # Search for the project in the workspace
        workspace_dir = get_workspace(self.config)
        
        for project_dir in os.listdir(workspace_dir):
            project_path = os.path.join(workspace_dir, project_dir)
            
            if os.path.isdir(project_path):
                json_path = os.path.join(project_path, 'project.json')
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            project_data = json.load(f)
                            if project_data.get("id") == project_id:
                                # Convert the dictionary to a Project object for compatibility
                                return Project(**project_data)
                    except Exception as e:
                        logger.error(f"Error loading project from {json_path}: {str(e)}")
        
        raise ProjectNotFoundError(f"Project with ID {project_id} not found")

    async def list_projects(self) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all projects.
        """
        projects = []
        workspace_dir = get_workspace(self.config)
        
        for project_dir in os.listdir(workspace_dir):
            project_path = os.path.join(workspace_dir, project_dir)
            
            if os.path.isdir(project_path):
                json_path = os.path.join(project_path, 'project.json')
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            project_data = json.load(f)
                            # Convert the dictionary to a Project object for compatibility
                            projects.append(Project(**project_data))
                    except Exception as e:
                        logger.error(f"Error loading project from {json_path}: {str(e)}")
        
        return projects

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
        from roboco.core.project_fs import ProjectFS
        
        # Create the project using ProjectFS directly
        project_fs = ProjectFS.initialize(
            name=name,
            description=description,
            directory=directory,
            teams=teams,
            tags=tags
        )
        
        # Get and return the project
        project_data = project_fs.get_project()
        # Convert to Project object for compatibility
        return Project(**project_data)

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
        # Find the project directory
        project_directory = await self.get_project_directory(project_id)
        if not project_directory:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        
        # Create ProjectFS instance
        project_fs = ProjectFS(project_dir=project_directory)
        
        # Get the project data
        project_data = project_fs.get_project()
        
        # Get task information from tasks.md
        tasks_content = ""
        if project_fs.exists_sync("tasks.md"):
            tasks_content = project_fs.read_sync("tasks.md")
        
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
            "id": project_data["id"],
            "name": project_data["name"],
            "description": project_data["description"],
            "status": "completed" if completed_tasks == total_tasks and total_tasks > 0 else "in_progress",
            "progress": round(progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "created_at": project_data["created_at"],
            "updated_at": project_data["updated_at"],
            "directory": project_data["directory"],
            "path": str(project_fs.base_dir)
        }

    async def find_projects_by_name(self, name: str) -> List[Project]:
        """
        Find projects by name.
        
        Args:
            name: Name to search for (case-insensitive partial match).
            
        Returns:
            List of projects matching the name.
        """
        projects = []
        workspace_dir = get_workspace(self.config)
        name_lower = name.lower()
        
        for project_dir in os.listdir(workspace_dir):
            project_path = os.path.join(workspace_dir, project_dir)
            
            if os.path.isdir(project_path):
                json_path = os.path.join(project_path, 'project.json')
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            project_data = json.load(f)
                            # Check if name matches
                            if name_lower in project_data.get("name", "").lower():
                                # Convert the dictionary to a Project object for compatibility
                                projects.append(Project(**project_data))
                    except Exception as e:
                        logger.error(f"Error loading project from {json_path}: {str(e)}")
        
        return projects

    async def get_project_directory(self, project_id: str) -> Optional[str]:
        """
        Get the directory name for a project by its ID.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The directory name of the project, or None if not found.
        """
        try:
            # Get all projects and find the one with matching ID
            workspace_dir = get_workspace(self.config)
            
            for project_dir in os.listdir(workspace_dir):
                project_path = os.path.join(workspace_dir, project_dir)
                
                if os.path.isdir(project_path):
                    json_path = os.path.join(project_path, 'project.json')
                    
                    if os.path.exists(json_path):
                        try:
                            with open(json_path, 'r') as f:
                                project_data = json.load(f)
                                if project_data.get("id") == project_id:
                                    return project_data.get("directory")
                        except Exception:
                            pass
            return None
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
        from roboco.core.project_fs import ProjectFS
        
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
        project_data = project_fs.get_project()
        
        # Add ID if not present
        if "id" not in project_data:
            project_data["id"] = generate_short_id()
            logger.info(f"Added missing ID {project_data['id']} to newly created project")
            
        # Ensure metadata dict exists
        if "metadata" not in project_data:
            project_data["metadata"] = {}
            
        # Add metadata if provided
        if metadata:
            project_data["metadata"].update(metadata)
        
        project_data["metadata"]["summary"] = planning_result.get("summary", "")
        project_data["metadata"]["created_at"] = datetime.now().isoformat()
        
        # Save updates
        project_fs.save_project(project_data)
        
        # Convert to Project object for compatibility
        return Project(**project_data)
    