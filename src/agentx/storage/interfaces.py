"""
Storage interfaces - Clean abstractions for different types of storage operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, BinaryIO
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass


@dataclass
class StorageResult:
    """Result of a storage operation."""
    success: bool
    path: Optional[str] = None
    size: Optional[int] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.data is None:
            self.data = {}


@dataclass
class FileInfo:
    """Information about a stored file."""
    path: str
    size: int
    created_at: datetime
    modified_at: datetime
    content_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StorageBackend(ABC):
    """Base interface for all storage backends."""
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if a path exists."""
        pass
    
    @abstractmethod
    async def get_info(self, path: str) -> Optional[FileInfo]:
        """Get information about a file/directory."""
        pass
    
    @abstractmethod
    async def list_directory(self, path: str = ".") -> List[FileInfo]:
        """List contents of a directory."""
        pass


class FileStorage(StorageBackend):
    """Interface for file storage operations."""
    
    @abstractmethod
    async def read_text(self, path: str, encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        pass
    
    @abstractmethod
    async def write_text(self, path: str, content: str, encoding: str = "utf-8") -> StorageResult:
        """Write text content to a file."""
        pass
    
    @abstractmethod
    async def read_bytes(self, path: str) -> bytes:
        """Read binary content from a file."""
        pass
    
    @abstractmethod
    async def write_bytes(self, path: str, content: bytes) -> StorageResult:
        """Write binary content to a file."""
        pass
    
    @abstractmethod
    async def append_text(self, path: str, content: str, encoding: str = "utf-8") -> StorageResult:
        """Append text content to a file."""
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> StorageResult:
        """Delete a file."""
        pass
    
    @abstractmethod
    async def create_directory(self, path: str) -> StorageResult:
        """Create a directory."""
        pass


class ArtifactStorage(StorageBackend):
    """Interface for artifact storage with versioning and metadata."""
    
    @abstractmethod
    async def store_artifact(
        self, 
        name: str, 
        content: Union[str, bytes], 
        content_type: str = "text/plain",
        metadata: Optional[Dict[str, Any]] = None
    ) -> StorageResult:
        """Store an artifact with versioning."""
        pass
    
    @abstractmethod
    async def get_artifact(self, name: str, version: Optional[str] = None) -> Optional[str]:
        """Get artifact content by name and optional version."""
        pass
    
    @abstractmethod
    async def list_artifacts(self) -> List[Dict[str, Any]]:
        """List all artifacts with their metadata."""
        pass
    
    @abstractmethod
    async def get_artifact_versions(self, name: str) -> List[str]:
        """Get all versions of an artifact."""
        pass
    
    @abstractmethod
    async def delete_artifact(self, name: str, version: Optional[str] = None) -> StorageResult:
        """Delete an artifact or specific version."""
        pass 