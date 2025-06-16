"""
Storage factory - Creates storage providers using factory pattern.

Separates pure filesystem abstraction from business logic.
"""

from typing import Union
from pathlib import Path

from .interfaces import FileStorage
from .backends import LocalFileStorage
from .workspace import WorkspaceStorage
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StorageFactory:
    """
    Factory for creating storage providers.
    
    Creates filesystem abstractions that can be swapped for different backends
    (local, S3, Azure, etc.) and workspace storage for business logic.
    """
    
    @staticmethod
    def create_file_storage(base_path: Union[str, Path]) -> FileStorage:
        """
        Create a filesystem abstraction.
        
        This can be swapped for different backends like S3FileStorage,
        AzureFileStorage, etc. without changing the business logic.
        
        Args:
            base_path: Base path for the filesystem
            
        Returns:
            FileStorage implementation
        """
        base_path = Path(base_path)
        base_path.mkdir(parents=True, exist_ok=True)
        
        provider = LocalFileStorage(base_path)
        logger.info(f"Created file storage provider: {base_path}")
        return provider
    
    @staticmethod
    def create_workspace_storage(
        workspace_path: Union[str, Path], 
        use_git_artifacts: bool = True
    ) -> WorkspaceStorage:
        """
        Create a workspace storage for business logic.
        
        Handles business concepts like artifacts, messages, execution plans
        using the filesystem abstraction underneath.
        
        Args:
            workspace_path: Path to the workspace directory
            use_git_artifacts: Whether to use Git for artifact versioning
            
        Returns:
            WorkspaceStorage instance
        """
        workspace_path = Path(workspace_path)
        workspace_path.mkdir(parents=True, exist_ok=True)
        
        # Create the filesystem abstraction
        file_storage = StorageFactory.create_file_storage(workspace_path)
        
        # Create the workspace with business logic
        workspace = WorkspaceStorage(workspace_path, file_storage, use_git_artifacts)
        logger.info(f"Created workspace storage: {workspace_path} (Git artifacts: {use_git_artifacts})")
        return workspace 