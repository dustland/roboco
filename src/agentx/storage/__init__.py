"""
AgentX Storage - Clean persistence abstractions for the framework.

Provides storage backends and interfaces that can be used directly by the framework
and wrapped as tools for LLM agents.
"""

from .interfaces import StorageBackend, FileStorage, ArtifactStorage, StorageResult
from .backends import LocalFileStorage
from .factory import StorageFactory
from .workspace import WorkspaceStorage
from .git_storage import GitArtifactStorage

__all__ = [
    "StorageBackend",
    "FileStorage", 
    "ArtifactStorage",
    "StorageResult",
    "LocalFileStorage",
    "StorageFactory",
    "WorkspaceStorage",
    "GitArtifactStorage"
] 