"""
Storage subsystem models - Self-contained data models for storage management.

This module contains all data models related to storage management, following the
architectural rule that subsystems should be self-contained and not import from core.
"""

from typing import Dict, List, Optional, Any, Union, Literal, BinaryIO
from datetime import datetime
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

# Internal utilities (avoid importing from core/utils)
import secrets
import string

def generate_short_id(length: int = 8) -> str:
    """Generate a short, URL-friendly, cryptographically secure random ID."""
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============================================================================
# STORAGE TYPE DEFINITIONS
# ============================================================================

class StorageBackendType(str, Enum):
    """Types of storage backends."""
    LOCAL = "local"
    GIT = "git"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GCS = "gcs"
    MEMORY = "memory"


class ArtifactType(str, Enum):
    """Types of artifacts that can be stored."""
    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    IMAGE = "image"
    DOCUMENT = "document"
    CODE = "code"
    DATA = "data"
    LOG = "log"
    REPORT = "report"
    CONFIG = "config"


class StorageOperation(str, Enum):
    """Types of storage operations."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    COPY = "copy"
    MOVE = "move"
    SYNC = "sync"


class FileStatus(str, Enum):
    """File status in storage."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    UNCHANGED = "unchanged"
    CONFLICT = "conflict"


# ============================================================================
# CORE STORAGE MODELS
# ============================================================================

class Artifact(BaseModel):
    """Represents a stored artifact."""
    artifact_id: str = Field(default_factory=lambda: f"art_{generate_short_id()}")
    name: str
    path: str
    artifact_type: ArtifactType
    
    # Content metadata
    size_bytes: int = 0
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    checksum: Optional[str] = None
    
    # Storage metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None  # agent name
    version: int = 1
    
    # Context metadata
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "name": self.name,
            "path": self.path,
            "artifact_type": self.artifact_type.value,
            "size_bytes": self.size_bytes,
            "mime_type": self.mime_type,
            "encoding": self.encoding,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "version": self.version,
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "tool_name": self.tool_name,
            "metadata": self.metadata,
            "tags": self.tags
        }


class ArtifactContent(BaseModel):
    """Content of an artifact."""
    artifact_id: str
    content: Union[str, bytes]
    content_type: str  # "text", "binary"
    encoding: Optional[str] = None
    
    def get_text_content(self) -> str:
        """Get content as text."""
        if self.content_type == "text":
            return self.content if isinstance(self.content, str) else self.content.decode(self.encoding or 'utf-8')
        raise ValueError("Cannot get text content from binary artifact")
    
    def get_binary_content(self) -> bytes:
        """Get content as bytes."""
        if self.content_type == "binary":
            return self.content if isinstance(self.content, bytes) else self.content.encode(self.encoding or 'utf-8')
        if self.content_type == "text":
            return self.content.encode(self.encoding or 'utf-8') if isinstance(self.content, str) else self.content
        raise ValueError("Cannot get binary content")


# ============================================================================
# STORAGE BACKEND INTERFACE
# ============================================================================

class StorageBackend(ABC):
    """Abstract interface for storage backend implementations."""
    
    @abstractmethod
    async def store(self, path: str, content: Union[str, bytes], 
                   artifact_type: ArtifactType = ArtifactType.TEXT,
                   metadata: Dict[str, Any] = None) -> Artifact:
        """Store content at the specified path."""
        pass
    
    @abstractmethod
    async def retrieve(self, path: str) -> Optional[ArtifactContent]:
        """Retrieve content from the specified path."""
        pass
    
    @abstractmethod
    async def delete(self, path: str) -> bool:
        """Delete content at the specified path."""
        pass
    
    @abstractmethod
    async def list_artifacts(self, prefix: str = "", 
                           artifact_type: Optional[ArtifactType] = None,
                           limit: int = 100) -> List[Artifact]:
        """List artifacts with optional filtering."""
        pass
    
    @abstractmethod
    async def get_artifact(self, artifact_id: str) -> Optional[Artifact]:
        """Get artifact metadata by ID."""
        pass
    
    @abstractmethod
    async def update_metadata(self, artifact_id: str, metadata: Dict[str, Any]) -> bool:
        """Update artifact metadata."""
        pass
    
    @abstractmethod
    async def copy(self, source_path: str, dest_path: str) -> bool:
        """Copy artifact from source to destination."""
        pass
    
    @abstractmethod
    async def move(self, source_path: str, dest_path: str) -> bool:
        """Move artifact from source to destination."""
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if artifact exists at path."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> 'StorageStats':
        """Get storage backend statistics."""
        pass
    
    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Get storage backend health information."""
        pass


# ============================================================================
# WORKSPACE MODELS
# ============================================================================

class WorkspaceConfig(BaseModel):
    """Configuration for a workspace."""
    workspace_id: str = Field(default_factory=lambda: f"ws_{generate_short_id()}")
    name: str
    path: str
    description: Optional[str] = None
    
    # Storage configuration
    backend: StorageBackendType = StorageBackendType.LOCAL
    backend_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Workspace settings
    auto_commit: bool = True
    auto_sync: bool = False
    max_size_mb: Optional[int] = None
    retention_days: Optional[int] = None
    
    # Access control
    read_only: bool = False
    allowed_agents: Optional[List[str]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceState(BaseModel):
    """Current state of a workspace."""
    workspace_id: str
    total_artifacts: int = 0
    total_size_bytes: int = 0
    last_activity: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    
    # File system state
    file_count: int = 0
    directory_count: int = 0
    
    # Version control state (for Git backend)
    current_branch: Optional[str] = None
    last_commit: Optional[str] = None
    uncommitted_changes: int = 0
    
    # Health status
    status: str = "healthy"  # "healthy", "degraded", "error"
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# FILE SYSTEM MODELS
# ============================================================================

class FileInfo(BaseModel):
    """Information about a file in storage."""
    path: str
    name: str
    size_bytes: int
    is_directory: bool = False
    
    # Timestamps
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    accessed_at: Optional[datetime] = None
    
    # File properties
    mime_type: Optional[str] = None
    encoding: Optional[str] = None
    permissions: Optional[str] = None
    
    # Content metadata
    line_count: Optional[int] = None
    checksum: Optional[str] = None
    
    # Context
    artifact_id: Optional[str] = None
    artifact_type: Optional[ArtifactType] = None


class DirectoryListing(BaseModel):
    """Listing of directory contents."""
    path: str
    files: List[FileInfo]
    directories: List[FileInfo]
    total_size_bytes: int = 0
    file_count: int = 0
    directory_count: int = 0
    
    def get_all_items(self) -> List[FileInfo]:
        """Get all files and directories combined."""
        return self.files + self.directories


# ============================================================================
# VERSION CONTROL MODELS
# ============================================================================

class CommitInfo(BaseModel):
    """Information about a commit."""
    commit_id: str
    message: str
    author: str
    timestamp: datetime
    parent_commits: List[str] = Field(default_factory=list)
    
    # Changed files
    added_files: List[str] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    deleted_files: List[str] = Field(default_factory=list)
    
    # Metadata
    branch: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BranchInfo(BaseModel):
    """Information about a branch."""
    name: str
    commit_id: str
    is_current: bool = False
    is_default: bool = False
    
    # Branch metadata
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    last_commit_at: Optional[datetime] = None
    
    # Tracking information
    upstream_branch: Optional[str] = None
    ahead_count: int = 0
    behind_count: int = 0


class FileChange(BaseModel):
    """Represents a change to a file."""
    path: str
    status: FileStatus
    old_path: Optional[str] = None  # For renames/moves
    
    # Change metadata
    lines_added: int = 0
    lines_removed: int = 0
    size_change: int = 0
    
    # Context
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    change_reason: Optional[str] = None


# ============================================================================
# STORAGE OPERATIONS MODELS
# ============================================================================

class StorageOperation(BaseModel):
    """Represents a storage operation."""
    operation_id: str = Field(default_factory=lambda: f"op_{generate_short_id()}")
    operation_type: StorageOperation
    path: str
    
    # Operation details
    source_path: Optional[str] = None  # For copy/move operations
    content_size: int = 0
    
    # Context
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    # Execution
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StorageOperationResult(BaseModel):
    """Result of a storage operation."""
    operation_id: str
    success: bool
    artifact: Optional[Artifact] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    bytes_processed: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# STORAGE STATISTICS AND MONITORING
# ============================================================================

class StorageStats(BaseModel):
    """Storage backend statistics."""
    backend_type: str
    total_artifacts: int = 0
    total_size_bytes: int = 0
    
    # Artifact breakdown
    artifacts_by_type: Dict[str, int] = Field(default_factory=dict)
    size_by_type: Dict[str, int] = Field(default_factory=dict)
    
    # Activity stats
    operations_today: int = 0
    operations_total: int = 0
    last_operation: Optional[datetime] = None
    
    # Performance stats
    avg_read_time_ms: float = 0.0
    avg_write_time_ms: float = 0.0
    cache_hit_rate: float = 0.0
    
    # Storage health
    available_space_bytes: Optional[int] = None
    used_space_bytes: Optional[int] = None
    error_count: int = 0
    warning_count: int = 0


class StorageHealth(BaseModel):
    """Storage backend health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    backend_type: str
    
    # Connectivity
    connection_status: bool = True
    last_successful_operation: Optional[datetime] = None
    
    # Performance
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    
    # Capacity
    disk_usage_percent: Optional[float] = None
    available_space_gb: Optional[float] = None
    
    # Issues
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    
    # Metadata
    last_check: datetime = Field(default_factory=datetime.now)
    uptime_seconds: float = 0.0


# ============================================================================
# STORAGE CONFIGURATION MODELS
# ============================================================================

class StorageConfig(BaseModel):
    """Configuration for storage system."""
    backend: StorageBackendType = StorageBackendType.LOCAL
    
    # Backend-specific configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # General settings
    workspace_path: str = "./workspace"
    max_file_size_mb: int = 100
    allowed_extensions: Optional[List[str]] = None
    blocked_extensions: List[str] = Field(default_factory=lambda: ['.exe', '.bat', '.sh'])
    
    # Performance settings
    cache_enabled: bool = True
    cache_size_mb: int = 100
    compression_enabled: bool = False
    
    # Backup settings
    backup_enabled: bool = False
    backup_interval_hours: int = 24
    backup_retention_days: int = 30
    
    # Security settings
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    
    # Monitoring
    metrics_enabled: bool = True
    health_check_interval_seconds: int = 300


# ============================================================================
# SEARCH AND INDEXING MODELS
# ============================================================================

class SearchQuery(BaseModel):
    """Query for searching artifacts."""
    query: str
    artifact_types: Optional[List[ArtifactType]] = None
    path_pattern: Optional[str] = None
    
    # Filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    size_min: Optional[int] = None
    size_max: Optional[int] = None
    tags: Optional[List[str]] = None
    
    # Context filters
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    created_by: Optional[str] = None
    
    # Search options
    include_content: bool = False
    limit: int = 100
    offset: int = 0


class SearchResult(BaseModel):
    """Result from artifact search."""
    artifacts: List[Artifact]
    total_count: int
    query_time_ms: float
    has_more: bool = False
    
    # Search metadata
    query: str
    filters_applied: List[str] = Field(default_factory=list)
    search_metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# STORAGE UTILITIES
# ============================================================================

def create_artifact(name: str, path: str, artifact_type: ArtifactType,
                   content_size: int = 0, created_by: str = None,
                   task_id: str = None, agent_name: str = None,
                   metadata: Dict[str, Any] = None) -> Artifact:
    """Create a new artifact with the specified parameters."""
    return Artifact(
        name=name,
        path=path,
        artifact_type=artifact_type,
        size_bytes=content_size,
        created_by=created_by,
        task_id=task_id,
        agent_name=agent_name,
        metadata=metadata or {}
    )


def get_mime_type(file_path: str) -> str:
    """Get MIME type for a file based on its extension."""
    import mimetypes
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def calculate_checksum(content: Union[str, bytes]) -> str:
    """Calculate SHA-256 checksum of content."""
    import hashlib
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB" 