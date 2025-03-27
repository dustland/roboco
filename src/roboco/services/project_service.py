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
from roboco.core.project import Project
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
            project_id: The ID of the project to retrieve
            
        Returns:
            The Project with the specified ID.
            
        Raises:
            ProjectNotFoundError: If the project cannot be found.
        """
        try:
            # Load the project directly using the project_id
            return Project.load(project_id)
        except ProjectNotFoundError:
            raise ProjectNotFoundError(f"Project with ID {project_id} not found")
        except Exception as e:
            logger.error(f"Error loading project {project_id}: {str(e)}")
            raise ProjectNotFoundError(f"Project with ID {project_id} not found: {str(e)}")

    async def list_projects(self) -> List[Project]:
        """
        List all projects.
        
        Returns:
            List of all projects.
        """
        projects = []
        workspace_dir = get_workspace(self.config)
        
        for project_id in os.listdir(workspace_dir):
            project_path = os.path.join(workspace_dir, project_id)
            
            if os.path.isdir(project_path):
                json_path = os.path.join(project_path, 'project.json')
                
                if os.path.exists(json_path):
                    try:
                        # Load the project using Project.load
                        project = Project.load(project_id)
                        projects.append(project)
                    except Exception as e:
                        logger.error(f"Error loading project from {json_path}: {str(e)}")
        
        return projects

    async def create_project(
        self,
        name: str,
        description: str,
        project_id: Optional[str] = None,
        teams: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Name of the project.
            description: Description of the project.
            project_id: Custom project ID (optional, defaults to 'project_{id}')
            teams: Teams involved in the project (optional).
            tags: Tags for the project (optional).
            
        Returns:
            The newly created Project.
        """
        # Generate a unique ID for the project
        generated_id = generate_short_id()
        
        # Use the generated ID if no custom ID is provided
        if not project_id:
            project_id = f"project_{generated_id}"
        
        # Create the project using Project.initialize
        project = Project.initialize(
            name=name,
            description=description,
            project_id=project_id,
            teams=teams
        )
        
        return project

    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get the status of a project including task completion status.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dictionary with project status information.
            
        Raises:
            ProjectNotFoundError: If the project cannot be found.
        """
        # Create ProjectFS instance directly using the project_id
        project_fs = ProjectFS(project_id=project_id)
        
        # Get the project data
        try:
            project_data = project_fs.read_json_sync("project.json")
        except FileNotFoundError:
            raise ProjectNotFoundError(f"Project file not found at {project_id}/project.json")
        except json.JSONDecodeError:
            raise ProjectNotFoundError(f"Invalid JSON in project file at {project_id}/project.json")
        
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
            "id": project_id,
            "name": project_data["name"],
            "description": project_data["description"],
            "status": "completed" if completed_tasks == total_tasks and total_tasks > 0 else "in_progress",
            "progress": round(progress, 2),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "created_at": project_data["created_at"],
            "updated_at": project_data["updated_at"],
            "project_id": project_id,
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
        
        for project_id in os.listdir(workspace_dir):
            project_path = os.path.join(workspace_dir, project_id)
            
            if os.path.isdir(project_path):
                json_path = os.path.join(project_path, 'project.json')
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            project_data = json.load(f)
                            # Check if name matches
                            if name_lower in project_data.get("name", "").lower():
                                try:
                                    # Load the project using Project.load
                                    project = Project.load(project_id)
                                    projects.append(project)
                                except Exception as e:
                                    logger.error(f"Error loading project: {str(e)}")
                    except Exception as e:
                        logger.error(f"Error reading project data from {json_path}: {str(e)}")
        
        return projects

    async def create_project_from_query(
        self, 
        query: str, 
        teams: Optional[List[str]] = None, 
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None
    ) -> Project:
        """
        Create a project from a natural language query.
        
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
        # Generate a unique project ID early if not provided
        if not project_id:
            project_id = generate_short_id()
            logger.info(f"Generated project ID: {project_id}")
        
        # Log the start of project creation
        logger.info(f"Creating project from query: {query} with ID: {project_id}")
        
        # Create planning team with workspace directory
        planning_team = PlanningTeam(project_id=project_id)
        
        # Prepare planning context with provided project_id
        planning_context = {
            "project_id": project_id,
            "query": query
        }
        
        # Get planning result - let exceptions propagate
        planning_result = await planning_team.run_chat(
            query=query,
            teams=teams,
            context=planning_context
        )
        
        # Use the provided project_id or find it in planning result as fallback
        project_id_to_use = project_id
        if not project_id_to_use:
            project_id_to_use = planning_result.get("project_id") or planning_result.get("project_dir")
            if not project_id_to_use:
                # Use the project ID as the directory name
                project_id_to_use = f"project_{generate_short_id()}"
                logger.info(f"No project_id in planning result, using generated name: {project_id_to_use}")
        
        # Load the project to append and update metadata
        project = Project.load(project_id_to_use)
        
        # Add metadata if provided
        if metadata:
            for key, value in metadata.items():
                project.update_metadata(key, value)
        
        # Add summary from planning result
        project.update_metadata("summary", planning_result.get("summary", ""))
        project.update_metadata("created_from_query", query)
        project.update_metadata("created_at", datetime.now().isoformat())
        
        # Save the project
        project.save()
        
        return project 