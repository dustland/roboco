"""
Workspace Management

This module provides functionality for managing a workspace containing
research artifacts, development code, and documentation for roboco agents.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from roboco.core.logger import get_logger
from roboco.core.config import load_config
from roboco.core.project_fs import ProjectFS, ProjectNotFoundError

logger = get_logger(__name__)

class Workspace:
    """Manages a workspace for research and development artifacts."""
    
    @classmethod
    def create_from_config(cls, config_path: Optional[str] = None) -> 'Workspace':
        """Create a workspace from configuration.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Workspace: Initialized workspace instance
        """
        from roboco.core import get_workspace
        
        config = load_config(config_path)
        workspace_path = get_workspace(config)
        
        return cls(str(workspace_path))
    
    def __init__(self, root_path: str):
        """Initialize the workspace.
        
        Args:
            root_path: Root path for the workspace.
        """
        self.root_path = Path(root_path).resolve()
        
        # Define standard workspace directories
        self.research_path = self.root_path / "research"
        self.code_path = self.root_path / "code"
        self.docs_path = self.root_path / "docs"
        self.data_path = self.root_path / "data"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        logger.info(f"Initialized workspace at {self.root_path}")
    
    def _ensure_directories(self):
        """Ensure that all necessary directories exist.
        
        Uses a helper method to avoid direct os.makedirs calls.
        """
        self._ensure_directory(self.research_path)
        self._ensure_directory(self.code_path)
        self._ensure_directory(self.docs_path)
        self._ensure_directory(self.data_path)
    
    def _ensure_directory(self, directory_path: Path):
        """Ensure a directory exists.
        
        Args:
            directory_path: Path to ensure exists
        """
        directory_path.mkdir(parents=True, exist_ok=True)
    
    def get_research_path(self, topic_name: Optional[str] = None) -> Path:
        """Get the path to a research topic, or the research directory.
        
        Args:
            topic_name: Name of the research topic, or None for the research directory.
            
        Returns:
            Path: Path to the research topic or directory.
        """
        if topic_name:
            path = self.research_path / topic_name
            self._ensure_directory(path)
            return path
        return self.research_path
    
    async def get_project_path(self, project_name: str) -> Path:
        """Get the path to a project.
        
        This method tries to find a project by name or ID.
        
        Args:
            project_name: Name or ID of the project.
            
        Returns:
            Path: Path to the project.
        """
        try:
            # Try to get the project by ID first
            project_fs = await ProjectFS.get_by_id(project_name)
            return project_fs.path
        except ProjectNotFoundError:
            # If not found by ID, try by name
            try:
                projects = await ProjectFS.find_by_name(project_name)
                if projects:
                    # Use the first matching project
                    project_fs = await ProjectFS.get_by_id(projects[0].id)
                    return project_fs.path
            except Exception:
                pass
        
        # If not found, use a default path based on the name
        config = load_config()
        return Path(os.path.join(config.workspace_root, "projects", project_name))
    
    def get_doc_path(self, doc_name: Optional[str] = None) -> Path:
        """Get the path to a document, or the docs directory.
        
        Args:
            doc_name: Name of the document, or None for the docs directory.
            
        Returns:
            Path: Path to the document or directory.
        """
        if doc_name:
            path = self.docs_path / doc_name
            self._ensure_directory(path)
            return path
        return self.docs_path
    
    def get_data_path(self, data_name: Optional[str] = None) -> Path:
        """Get the path to a data file or directory, or the data directory.
        
        Args:
            data_name: Name of the data file or directory, or None for the data directory.
            
        Returns:
            Path: Path to the data file/directory or the data directory.
        """
        if data_name:
            path = self.data_path / data_name
            self._ensure_directory(path)
            return path
        return self.data_path
    
    def create_research_topic(self, topic_name: str, description: str = "") -> Path:
        """Create a research topic directory with notes and resources.
        
        Args:
            topic_name: Name of the research topic.
            description: Description of the topic.
            
        Returns:
            Path: Path to the created research topic.
        """
        topic_path = self.get_research_path(topic_name)
        
        # Create standard subdirectories using helper method
        self._ensure_directory(topic_path / "notes")
        self._ensure_directory(topic_path / "resources")
        
        # Create a README.md file
        readme_path = topic_path / "README.md"
        with open(readme_path, 'w') as f:
            f.write(f"# {topic_name}\n\n{description}\n\n")
            f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        logger.info(f"Created research topic at {topic_path}")
        return topic_path
    
    async def create_project_structure(self, project_name: str, structure: Dict[str, Any]) -> Path:
        """Create a project structure in the workspace.
        
        Use ProjectFS to create the project directories and files.
        
        Args:
            project_name: Name of the project.
            structure: Dictionary defining the project structure.
            
        Returns:
            Path: Path to the project directory.
        """
        # Create a project using ProjectFS
        project_fs = await ProjectFS.create(
            name=project_name,
            description=f"Project {project_name}",
            directory=project_name.lower().replace(" ", "_"),
        )
        
        # Create the directory structure and files
        for dir_path, files in structure.items():
            # Ensure directory exists
            await project_fs.mkdir(dir_path)
            
            # Create each file
            for file_name, content in files.items():
                file_path = os.path.join(dir_path, file_name)
                await project_fs.write(file_path, content)
        
        logger.info(f"Created project structure at {project_fs.path}")
        return project_fs.path
    
    async def list_projects(self) -> List[str]:
        """List all projects in the workspace.
        
        Returns:
            List[str]: List of project names.
        """
        projects = await ProjectFS.list_all()
        return [project.name for project in projects]
    
    def list_research_topics(self) -> List[str]:
        """List all research topics in the workspace.
        
        Returns:
            List[str]: List of research topic names.
        """
        return [p.name for p in self.research_path.iterdir() if p.is_dir()]
    
    def save_file(self, file_path: str, content: str) -> Path:
        """Save content to a file in the workspace.
        
        Args:
            file_path: Path to the file, relative to the workspace root.
            content: Content to write to the file.
            
        Returns:
            Path: Path to the saved file.
        """
        full_path = self.root_path / file_path
        
        # Ensure parent directory exists
        self._ensure_directory(full_path.parent)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Saved file {full_path}")
        return full_path
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file in the workspace.
        
        Args:
            file_path: Path to the file, relative to the workspace root.
            
        Returns:
            Optional[str]: Content of the file, or None if the file doesn't exist.
        """
        full_path = self.root_path / file_path
        
        if not full_path.exists():
            return None
        
        try:
            with open(full_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {full_path}: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up temporary files in the workspace."""
        # Implement cleanup logic here if needed
        pass 