"""
Project Manager Module

This module provides functionality for managing projects, including their tasks
and associated teams and jobs.
"""

from datetime import datetime
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from loguru import logger

from roboco.core.models.project import Project
from roboco.core.project_fs import ProjectFS, ProjectNotFoundError
from roboco.core.config import load_config, get_workspace
from roboco.core.task_manager import TaskManager
from roboco.core.models.project_manifest import ProjectManifest, ProjectFile

# Add module context to logger
logger = logger.bind(module=__name__)


class ProjectManager:
    """
    Manager for handling projects, tasks, and teams.
    
    This class provides methods for creating, retrieving, and updating projects,
    as well as for managing project tasks, file systems, and task execution.
    It combines project management, task execution, and workspace management
    into a single unified interface.
    """
    
    def __init__(self, config=None):
        """
        Initialize the project manager.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or load_config()
        self.workspace_dir = get_workspace()
        
        # Create required directories
        self._ensure_directories()
        
        # Load existing projects
        self._load_projects()
        
        logger.info(f"ProjectManager initialized with workspace: {self.workspace_dir}")
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        root_path = Path(self.workspace_dir)
        
        # Create key directories
        directories = [
            root_path,
            root_path / "projects",
            root_path / "research",
            root_path / "docs",
            root_path / "data"
        ]
        
        for directory in directories:
            self._ensure_directory(directory)
    
    def _ensure_directory(self, directory_path: Path):
        """Create a directory if it doesn't exist."""
        if not directory_path.exists():
            directory_path.mkdir(parents=True)
            logger.info(f"Created directory: {directory_path}")
    
    def _load_projects(self):
        """
        Load existing projects from the workspace.
        """
        self.projects = {}
        
        projects_dir = os.path.join(self.workspace_dir)
        if not os.path.exists(projects_dir):
            return
        
        for project_dir in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_dir)
            
            if os.path.isdir(project_path):
                json_path = os.path.join(project_path, 'project.json')
                
                if os.path.exists(json_path):
                    try:
                        with open(json_path, 'r') as f:
                            project_data = json.load(f)
                            # Store as dictionary, not Project object
                            self.projects[project_data["id"]] = project_data
                    except Exception as e:
                        logger.error(f"Error loading project from {json_path}: {str(e)}")
                        
        logger.info(f"Loaded {len(self.projects)} projects")
        
    async def _save_project(self, project_data: Dict[str, Any]):
        """
        Save project data to project.json.
        
        Args:
            project_data: Project data dictionary to save
        """
        project_dir = os.path.join(self.workspace_dir, project_data["project_dir"])
        os.makedirs(project_dir, exist_ok=True)
        
        json_path = os.path.join(project_dir, 'project.json')
        
        with open(json_path, 'w') as f:
            json.dump(project_data, f, indent=2)
            
        logger.info(f"Saved project data to {json_path}")
            
    async def _update_task_markdown(self, project_data: Dict[str, Any]):
        """
        Update the tasks.md file for a project.
        
        Args:
            project_data: Project data dictionary to update
        """
        from roboco.core.task_manager import TaskManager
        
        project_dir = os.path.join(self.workspace_dir, project_data["project_dir"])
        task_manager = TaskManager(fs=ProjectFS(project_dir=project_dir))
        
        tasks_md_path = os.path.join(project_dir, 'tasks.md')
        task_manager.save_tasks_md(tasks_md_path, project_data["tasks"])
        
        logger.info(f"Updated tasks.md file at {tasks_md_path}")
            
    async def create_project(
        self,
        manifest: Union[ProjectManifest, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a new project from a project manifest.
        
        This method now delegates to ProjectFS.initialize to avoid circular dependencies.
        
        Args:
            manifest: ProjectManifest object or dictionary containing manifest data
            
        Returns:
            Created project data dictionary
            
        Raises:
            ValueError: If required fields are missing or project directory already exists
        """
        from roboco.core.project_fs import ProjectFS
        
        # Log that we're creating a project
        logger.info(f"Creating project from manifest")
        
        # Create the project using ProjectFS.initialize
        project_fs = ProjectFS.initialize(manifest=manifest)
        
        # Get the project
        project_data = project_fs.get_project()
        
        # Add it to our projects dictionary
        self.projects[project_data["id"]] = project_data
        
        return project_data
        
    def get_project(self, project_id) -> Optional[Dict[str, Any]]:
        """
        Get a project by ID.
        
        Args:
            project_id: ID of the project
            
        Returns:
            Project data dictionary if found, None otherwise
        """
        return self.projects.get(project_id)
        
    def get_project_by_directory(self, project_dir) -> Optional[Dict[str, Any]]:
        """
        Get a project by directory name.
        
        Args:
            project_dir: Directory name of the project
            
        Returns:
            Project data dictionary if found, None otherwise
        """
        for project_data in self.projects.values():
            if project_data["project_dir"] == project_dir:
                return project_data
        return None
        
    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all projects.
        
        Returns:
            List of project data dictionaries
        """
        return list(self.projects.values())
        
    def find_projects_by_name(self, name) -> List[Dict[str, Any]]:
        """
        Find projects by name.
        
        Args:
            name: Project name to search for (case-insensitive partial match)
            
        Returns:
            List of matching project data dictionaries
        """
        name_lower = name.lower()
        return [p for p in self.projects.values() 
                if name_lower in p["name"].lower()]
        
    def find_projects_by_tag(self, tag) -> List[Dict[str, Any]]:
        """
        Find projects by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of matching project data dictionaries
        """
        return [p for p in self.projects.values() 
                if tag in p.get("tags", [])]
                
    async def update_project(self, project_id, **kwargs) -> Dict[str, Any]:
        """
        Update a project.
        
        Args:
            project_id: ID of the project to update
            **kwargs: Fields to update
            
        Returns:
            Updated project data dictionary
            
        Raises:
            ValueError: If project not found
        """
        project_data = self.get_project(project_id)
        
        if not project_data:
            raise ValueError(f"Project not found with ID: {project_id}")
            
        # Update fields
        for key, value in kwargs.items():
            if key in project_data:
                project_data[key] = value
                
        # Update timestamp
        project_data["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        await self._save_project(project_data)
        
        # Update tasks.md if tasks were updated
        if 'tasks' in kwargs:
            await self._update_task_markdown(project_data)
            
        logger.info(f"Updated project {project_id}")
        return project_data
        
    async def add_task(self, project_id, task) -> Dict[str, Any]:
        """
        Add a task to a project.
        
        Args:
            project_id: ID of the project
            task: Task object or dictionary
            
        Returns:
            Updated project data dictionary
            
        Raises:
            ValueError: If project not found
        """
        project_data = self.get_project(project_id)
        
        if not project_data:
            raise ValueError(f"Project not found with ID: {project_id}")
            
        # Create a task dictionary if needed
        if not isinstance(task, dict):
            task = task.dict()
            
        # Add the task
        project_data["tasks"].append(task)
        
        # Update timestamp
        project_data["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        await self._save_project(project_data)
        
        # Update tasks.md
        await self._update_task_markdown(project_data)
        
        logger.info(f"Added task to project {project_id}")
        return project_data
        
    async def update_task(self, project_id, task_id, **kwargs):
        """
        Update a task in a project.
        
        Args:
            project_id: ID of the project
            task_id: ID of the task
            **kwargs: Fields to update
            
        Returns:
            Updated project object
            
        Raises:
            ValueError: If project or task not found
        """
        project_data = self.get_project(project_id)
        
        if not project_data:
            raise ValueError(f"Project not found with ID: {project_id}")
            
        # Find the task
        task_index = None
        for i, task in enumerate(project_data["tasks"]):
            if task.get('id') == task_id:
                task_index = i
                break
                
        if task_index is None:
            raise ValueError(f"Task not found with ID: {task_id}")
            
        # Update fields
        for key, value in kwargs.items():
            project_data["tasks"][task_index][key] = value
            
        # Update timestamp
        project_data["updated_at"] = datetime.now().isoformat()
        
        # Save changes
        await self._save_project(project_data)
        
        # Update tasks.md
        await self._update_task_markdown(project_data)
        
        logger.info(f"Updated task {task_id} in project {project_id}")
        return project_data
        
    async def delete_project(self, project_id):
        """
        Delete a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if deleted, False otherwise
            
        Raises:
            ValueError: If project not found
        """
        project_data = self.get_project(project_id)
        
        if not project_data:
            raise ValueError(f"Project not found with ID: {project_id}")
            
        # Delete project directory
        project_dir = os.path.join(self.workspace_dir, project_data["project_dir"])
        
        if os.path.exists(project_dir):
            import shutil
            shutil.rmtree(project_dir)
            
        # Remove from projects dictionary
        del self.projects[project_id]
        
        logger.info(f"Deleted project {project_id}")
        return True

    # --- Methods from ProjectExecutor ---
    
    def get_executor(self, project_dir: str):
        """
        Get a task executor for a project.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            TaskManager instance
        """
        fs = ProjectFS(project_dir=project_dir)
        return TaskManager(fs=fs)
        
    async def execute_project(self, project_dir: str, keyword_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute all tasks in a project, optionally filtered by a keyword.
        
        Args:
            project_dir: Path to the project directory
            keyword_filter: Optional keyword to filter tasks by description
            
        Returns:
            Dictionary containing execution results
        """
        fs = ProjectFS(project_dir=project_dir)
        task_manager = TaskManager(fs=fs)
        
        # Parse tasks.md into tasks
        logger.info("Parsing tasks file")
        tasks = task_manager.load("tasks.md")
        
        if not tasks:
            error_msg = "No tasks found in tasks.md"
            logger.error(error_msg)
            return {"error": error_msg}
        
        logger.info(f"Found {len(tasks)} tasks in tasks.md")
        
        # Filter tasks if needed
        if keyword_filter:
            logger.info(f"Filtering tasks by keyword: {keyword_filter}")
            filtered_tasks = [t for t in tasks if keyword_filter.lower() in t.description.lower()]
            if not filtered_tasks:
                error_msg = f"No tasks matching '{keyword_filter}' found"
                logger.error(error_msg)
                return {"error": error_msg}
            tasks = filtered_tasks
            logger.info(f"Filtered to {len(tasks)} tasks")
        
        # Execute all tasks
        results = {
            "overall_status": "success",
            "directory_structure": {
                "root": project_dir,
            }
        }
        
        logger.info(f"Starting execution of {len(tasks)} tasks")
        
        # Execute tasks using the TaskManager
        task_results = await task_manager.execute_tasks(tasks)
        results.update(task_results)
        
        # Create a summary of files created in each directory
        src_files = fs.list_sync("src")
        docs_files = fs.list_sync("docs")
        
        results["files"] = {
            "src": src_files,
            "docs": docs_files
        }
        
        logger.info(f"Project execution completed with status: {results['overall_status']}")
        return results
        
    async def execute_task(self, project_dir: str, task_description: str) -> Dict[str, Any]:
        """Execute a specific task by description.
        
        Args:
            project_dir: Path to the project directory
            task_description: Title of the task to execute
            
        Returns:
            Dictionary with execution results
        """
        fs = ProjectFS(project_dir=project_dir)
        task_manager = TaskManager(fs=fs)
        
        # Get tasks.md path
        tasks_path = os.path.join(project_dir, "tasks.md")
        
        if not os.path.exists(tasks_path):
            error_msg = f"Tasks file not found at: {tasks_path}"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Parse tasks.md into tasks
        logger.info(f"Parsing tasks file: {tasks_path}")
        tasks = task_manager.load(tasks_path)
        
        if not tasks:
            error_msg = "No tasks found in tasks.md"
            logger.error(error_msg)
            return {"error": error_msg}
        
        # Find the task
        found_task = None
        for task in tasks:
            if task.description.lower() == task_description.lower():
                found_task = task
                break
        
        if found_task:
            logger.info(f"Found task '{task_description}'")
            
            # Execute the task using the TaskManager
            result = await task_manager.execute_task(found_task, tasks)
            
            return {
                "task": found_task.description,
                "result": result
            }
        
        # Task not found
        error_msg = f"Task '{task_description}' not found"
        logger.error(error_msg)
        return {"error": error_msg}
        
    # --- Methods from Workspace ---
    
    def get_research_path(self, topic_name: Optional[str] = None) -> Path:
        """Get the path to a research topic or the research directory.
        
        Args:
            topic_name: Optional name of the research topic
            
        Returns:
            Path to the research topic or directory
        """
        research_path = Path(self.workspace_dir) / "research"
        
        if topic_name:
            return research_path / topic_name
        
        return research_path
    
    async def get_project_path(self, project_name: str) -> Path:
        """Get the path to a project directory.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the project directory
            
        Raises:
            ProjectNotFoundError: If project not found
        """
        # Try direct match on directory name
        project_path = Path(self.workspace_dir) / project_name
        if project_path.exists() and project_path.is_dir():
            project_json = project_path / "project.json"
            if project_json.exists():
                return project_path
        
        # Try to find by name in projects dictionary
        for project_data in self.projects.values():
            if project_data["name"].lower() == project_name.lower() or project_data["project_dir"].lower() == project_name.lower():
                return Path(self.workspace_dir) / project_data["project_dir"]
        
        raise ProjectNotFoundError(f"Project not found: {project_name}")
    
    def get_doc_path(self, doc_name: Optional[str] = None) -> Path:
        """Get the path to a documentation file or the docs directory.
        
        Args:
            doc_name: Optional name of the documentation file
            
        Returns:
            Path to the documentation file or directory
        """
        docs_path = Path(self.workspace_dir) / "docs"
        
        if doc_name:
            return docs_path / doc_name
        
        return docs_path
    
    def get_data_path(self, data_name: Optional[str] = None) -> Path:
        """Get the path to a data file or the data directory.
        
        Args:
            data_name: Optional name of the data file
            
        Returns:
            Path to the data file or directory
        """
        data_path = Path(self.workspace_dir) / "data"
        
        if data_name:
            return data_path / data_name
        
        return data_path
    
    def create_research_topic(self, topic_name: str, description: str = "") -> Path:
        """Create a new research topic directory.
        
        Args:
            topic_name: Name of the research topic
            description: Optional description
            
        Returns:
            Path to the created research topic directory
        """
        research_path = self.get_research_path()
        topic_path = research_path / topic_name
        
        if topic_path.exists():
            logger.info(f"Research topic already exists: {topic_path}")
            return topic_path
        
        # Create the topic directory
        topic_path.mkdir(parents=True, exist_ok=True)
        
        # Create a README.md with the description
        readme_path = topic_path / "README.md"
        with open(readme_path, "w") as f:
            f.write(f"# {topic_name}\n\n{description}")
        
        logger.info(f"Created research topic: {topic_path}")
        return topic_path
    
    def save_file(self, file_path: str, content: str) -> Path:
        """Save content to a file.
        
        Args:
            file_path: Path to the file
            content: Content to save
            
        Returns:
            Path to the saved file
        """
        path = Path(file_path)
        
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            f.write(content)
        
        logger.info(f"Saved file: {path}")
        return path
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Content of the file, or None if the file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {path}: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up workspace resources."""
        logger.info(f"Cleaning up workspace: {self.workspace_dir}")