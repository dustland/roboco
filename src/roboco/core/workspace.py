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

logger = get_logger(__name__)

class Workspace:
    """Manages a workspace for research and development artifacts."""
    
    @classmethod
    def create_from_config(cls, config_path: Optional[str] = None) -> 'Workspace':
        """Create a workspace instance from configuration.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Workspace: Initialized workspace instance
        """
        from roboco.core.config import load_config, get_workspace
        
        config = load_config(config_path)
        workspace_path = get_workspace(config)
        
        return cls(str(workspace_path))
    
    def __init__(self, root_path: str):
        """Initialize the workspace.
        
        Args:
            root_path: Root path for the workspace.
        """
        self.root_path = Path(root_path).resolve()
        self.research_path = self.root_path / "research"
        self.code_path = self.root_path / "code"
        self.docs_path = self.root_path / "docs"
        self.data_path = self.root_path / "data"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        logger.info(f"Initialized workspace at {self.root_path}")
    
    def _ensure_directories(self):
        """Ensure that all necessary directories exist."""
        self.research_path.mkdir(parents=True, exist_ok=True)
        self.code_path.mkdir(parents=True, exist_ok=True)
        self.docs_path.mkdir(parents=True, exist_ok=True)
        self.data_path.mkdir(parents=True, exist_ok=True)
    
    def get_project_path(self, project_name: str) -> Path:
        """Get the path for a specific project.
        
        Args:
            project_name: Name of the project.
            
        Returns:
            Path: Path to the project directory.
        """
        project_name_safe = project_name.lower().replace(" ", "_").replace("-", "_")
        project_path = self.code_path / project_name_safe
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path
    
    def get_research_path(self, topic: str) -> Path:
        """Get the path for research on a specific topic.
        
        Args:
            topic: Research topic.
            
        Returns:
            Path: Path to the research directory.
        """
        topic_safe = topic.lower().replace(" ", "_").replace("-", "_")
        research_path = self.research_path / topic_safe
        research_path.mkdir(parents=True, exist_ok=True)
        return research_path
    
    def save_research_report(self, topic: str, report: Dict[str, Any]) -> Path:
        """Save a research report to the workspace.
        
        Args:
            topic: Research topic.
            report: Research report to save.
            
        Returns:
            Path: Path to the saved report.
        """
        import json
        
        research_path = self.get_research_path(topic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = research_path / f"report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Saved research report to {report_file}")
        return report_file
    
    def save_code_artifact(self, project_name: str, file_path: str, content: str) -> Path:
        """Save a code artifact to the workspace.
        
        Args:
            project_name: Name of the project.
            file_path: Relative path to the file within the project.
            content: Content to write to the file.
            
        Returns:
            Path: Path to the saved artifact.
        """
        project_path = self.get_project_path(project_name)
        full_path = project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(content)
        
        logger.info(f"Saved code artifact to {full_path}")
        return full_path
    
    def save_documentation(self, project_name: str, doc_name: str, content: str) -> Path:
        """Save documentation to the workspace.
        
        Args:
            project_name: Name of the project.
            doc_name: Name of the documentation file.
            content: Content to write to the file.
            
        Returns:
            Path: Path to the saved documentation.
        """
        project_name_safe = project_name.lower().replace(" ", "_").replace("-", "_")
        doc_path = self.docs_path / project_name_safe
        doc_path.mkdir(parents=True, exist_ok=True)
        
        doc_file = doc_path / f"{doc_name}.md"
        
        with open(doc_file, 'w') as f:
            f.write(content)
        
        logger.info(f"Saved documentation to {doc_file}")
        return doc_file
    
    def create_project_structure(self, project_name: str, structure: Dict[str, Any]) -> Path:
        """Create a project structure in the workspace.
        
        Args:
            project_name: Name of the project.
            structure: Dictionary defining the project structure.
            
        Returns:
            Path: Path to the project directory.
        """
        project_path = self.get_project_path(project_name)
        
        # Create directory structure
        for dir_path, files in structure.items():
            dir_full_path = project_path / dir_path
            dir_full_path.mkdir(parents=True, exist_ok=True)
            
            # Create files in the directory
            for file_name, content in files.items():
                file_path = dir_full_path / file_name
                
                with open(file_path, 'w') as f:
                    f.write(content)
        
        logger.info(f"Created project structure at {project_path}")
        return project_path
    
    def list_projects(self) -> List[str]:
        """List all projects in the workspace.
        
        Returns:
            List[str]: List of project names.
        """
        return [p.name for p in self.code_path.iterdir() if p.is_dir()]
    
    def list_research_topics(self) -> List[str]:
        """List all research topics in the workspace.
        
        Returns:
            List[str]: List of research topic names.
        """
        return [p.name for p in self.research_path.iterdir() if p.is_dir()]
    
    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get the content of a file in the workspace.
        
        Args:
            file_path: Path to the file, relative to the workspace root.
            
        Returns:
            Optional[str]: Content of the file, or None if the file doesn't exist.
        """
        full_path = self.root_path / file_path
        
        if not full_path.exists():
            logger.warning(f"File {full_path} does not exist")
            return None
        
        with open(full_path, 'r') as f:
            return f.read()
    
    def cleanup(self):
        """Clean up temporary files in the workspace."""
        # Implement any cleanup logic here
        pass 