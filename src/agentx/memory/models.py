"""
Memory subsystem models - Self-contained data models for memory management.

This module contains all data models related to memory management, following the
architectural rule that subsystems should be self-contained and not import from core.
"""

from typing import Dict, List, Optional, Any, Union, Literal, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from abc import ABC, abstractmethod

# Internal utilities (avoid importing from core/utils)
import secrets
import string

def generate_short_id(length: int = 8) -> str:
    """Generate a short, URL-friendly, cryptographically secure random ID."""
    alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


# ============================================================================
# MEMORY TYPE DEFINITIONS
# ============================================================================

class MemoryType(str, Enum):
    """Types of memory content."""
    TEXT = "text"
    JSON = "json"
    KEY_VALUE = "key_value"
    VERSIONED_TEXT = "versioned_text"
    # Specialized memory types for synthesis engine
    CONSTRAINT = "constraint"
    HOT_ISSUE = "hot_issue"
    DOCUMENT_CHUNK = "document_chunk"
    
    def __str__(self):
        return self.value


class MemoryBackendType(str, Enum):
    """Types of memory backends."""
    MEM0 = "mem0"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    LOCAL = "local"
    REDIS = "redis"


class MemoryOperation(str, Enum):
    """Types of memory operations."""
    ADD = "add"
    QUERY = "query"
    SEARCH = "search"
    UPDATE = "update"
    DELETE = "delete"
    CLEAR = "clear"
    SYNTHESIZE = "synthesize"


# ============================================================================
# CORE MEMORY DATA MODELS
# ============================================================================

@dataclass
class MemoryItem:
    """Individual memory item with metadata."""
    content: str
    memory_type: MemoryType
    agent_name: str
    memory_id: str = field(default_factory=lambda: generate_short_id())
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)
    source_event_id: Optional[str] = None
    is_active: bool = True
    version: Optional[int] = None
    parent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
            "importance": self.importance,
            "tags": self.tags,
            "source_event_id": self.source_event_id,
            "is_active": self.is_active,
            "version": self.version,
            "parent_id": self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItem':
        """Create MemoryItem from dictionary."""
        # Handle timestamp conversion
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        elif timestamp is None:
            timestamp = datetime.now()
        
        # Handle memory_type conversion
        memory_type = data.get("memory_type")
        if isinstance(memory_type, str):
            memory_type = MemoryType(memory_type)
        
        return cls(
            content=data["content"],
            memory_type=memory_type,
            agent_name=data["agent_name"],
            memory_id=data.get("memory_id", generate_short_id()),
            timestamp=timestamp,
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 1.0),
            tags=data.get("tags", []),
            source_event_id=data.get("source_event_id"),
            is_active=data.get("is_active", True),
            version=data.get("version"),
            parent_id=data.get("parent_id")
        )


# ============================================================================
# SYNTHESIS ENGINE MODELS
# ============================================================================

class Memory(BaseModel):
    """Base memory model for synthesis engine."""
    id: UUID = Field(default_factory=uuid4)
    type: Literal["CONSTRAINT", "HOT_ISSUE", "DOCUMENT_CHUNK"]
    content: str
    source_event_id: Optional[UUID] = None
    is_active: bool = True
    agent_name: str = "system"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    importance: float = 1.0


class Constraint(Memory):
    """Memory representing user constraints, preferences, or rules."""
    type: Literal["CONSTRAINT"] = "CONSTRAINT"
    # e.g., "Do not use requirements.txt", "Use APA citation style"
    constraint_category: Optional[str] = None
    enforcement_level: str = "strict"  # "strict", "prefer", "suggest"


class HotIssue(Memory):
    """Memory representing active problems that need attention."""
    type: Literal["HOT_ISSUE"] = "HOT_ISSUE"
    # e.g., "Unit test 'test_payment_flow' is failing"
    resolved_by_event_id: Optional[UUID] = None
    issue_category: Optional[str] = None
    severity: str = "medium"  # "low", "medium", "high", "critical"


class DocumentChunk(Memory):
    """Memory representing a chunk of document content for semantic search."""
    type: Literal["DOCUMENT_CHUNK"] = "DOCUMENT_CHUNK"
    source_file_path: str
    chunk_index: int = 0
    chunk_size: int = 0
    overlap_tokens: int = 0
    # e.g., A chunk of text from a file


# ============================================================================
# QUERY AND SEARCH MODELS
# ============================================================================

@dataclass
class MemoryQuery:
    """Query parameters for memory operations."""
    query: str
    memory_type: Optional[MemoryType] = None
    agent_name: Optional[str] = None
    max_tokens: Optional[int] = None
    limit: int = 10
    metadata_filter: Optional[Dict[str, Any]] = None
    importance_threshold: Optional[float] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    include_metadata: bool = True
    exclude_used_sources: bool = False
    semantic_similarity_threshold: float = 0.7
    rerank_results: bool = True


@dataclass
class MemorySearchResult:
    """Result from memory search operations."""
    items: List[MemoryItem]
    total_count: int
    query_time_ms: float
    has_more: bool = False
    query_metadata: Dict[str, Any] = field(default_factory=dict)
    similarity_scores: List[float] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "has_more": self.has_more,
            "query_metadata": self.query_metadata,
            "similarity_scores": self.similarity_scores
        }


# ============================================================================
# MEMORY BACKEND INTERFACE
# ============================================================================

class MemoryBackend(ABC):
    """Abstract interface for memory backend implementations."""
    
    @abstractmethod
    async def add(self, content: str, memory_type: MemoryType,
                  agent_name: str, metadata: dict = None,
                  importance: float = 1.0) -> str:
        """Add a new memory item."""
        pass
    
    @abstractmethod
    async def query(self, query: MemoryQuery) -> MemorySearchResult:
        """Query memories with structured parameters."""
        pass
    
    @abstractmethod
    async def search(self, query: MemoryQuery) -> MemorySearchResult:
        """Semantic search across memories."""
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, **kwargs) -> bool:
        """Update a memory item."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item."""
        pass
    
    @abstractmethod
    async def clear(self, agent_name: str = None) -> int:
        """Clear memories, optionally filtered by agent."""
        pass
    
    @abstractmethod
    async def count(self, **filters) -> int:
        """Count memories with optional filters."""
        pass
    
    @abstractmethod
    async def stats(self) -> 'MemoryStats':
        """Get memory backend statistics."""
        pass
    
    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Get backend health information."""
        pass


# ============================================================================
# MEMORY STATISTICS AND MONITORING
# ============================================================================

@dataclass
class MemoryStats:
    """Memory backend statistics."""
    total_memories: int
    memories_by_type: Dict[str, int]
    memories_by_agent: Dict[str, int]
    avg_importance: float
    oldest_memory: Optional[datetime] = None
    newest_memory: Optional[datetime] = None
    storage_size_mb: Optional[float] = None
    backend_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_memories": self.total_memories,
            "memories_by_type": self.memories_by_type,
            "memories_by_agent": self.memories_by_agent,
            "avg_importance": self.avg_importance,
            "oldest_memory": self.oldest_memory.isoformat() if self.oldest_memory else None,
            "newest_memory": self.newest_memory.isoformat() if self.newest_memory else None,
            "storage_size_mb": self.storage_size_mb,
            "backend_type": self.backend_type
        }


class MemoryHealth(BaseModel):
    """Memory backend health status."""
    status: str  # "healthy", "degraded", "unhealthy"
    backend_type: str
    connection_status: bool
    last_operation_time: Optional[datetime] = None
    error_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MEMORY CONFIGURATION MODELS
# ============================================================================

class MemoryConfig(BaseModel):
    """Configuration for memory system."""
    enabled: bool = True
    backend: MemoryBackendType = MemoryBackendType.MEM0
    
    # Backend-specific configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Memory behavior settings
    max_memories: Optional[int] = None
    retention_days: Optional[int] = None
    importance_threshold: float = 0.5
    
    # Synthesis settings
    synthesis_enabled: bool = True
    synthesis_interval: int = 3600  # seconds
    
    # Context injection settings
    context_enabled: bool = True
    max_context_memories: int = 10
    
    # Performance settings
    batch_size: int = 100
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds


# ============================================================================
# MEMORY OPERATIONS AND EVENTS
# ============================================================================

class MemoryOperationResult(BaseModel):
    """Result of a memory operation."""
    operation: MemoryOperation
    success: bool
    memory_id: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemoryEvent(BaseModel):
    """Event emitted by memory operations."""
    event_id: str = Field(default_factory=lambda: f"mem_{generate_short_id()}")
    operation: MemoryOperation
    agent_name: str
    memory_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MEMORY SYNTHESIS MODELS
# ============================================================================

class SynthesisRule(BaseModel):
    """Rule for memory synthesis."""
    name: str
    description: str
    conditions: Dict[str, Any]
    actions: List[str]
    priority: int = 0
    enabled: bool = True


class SynthesisResult(BaseModel):
    """Result of memory synthesis operation."""
    synthesis_id: str = Field(default_factory=lambda: f"syn_{generate_short_id()}")
    processed_memories: int
    new_memories: List[str] = Field(default_factory=list)
    updated_memories: List[str] = Field(default_factory=list)
    deleted_memories: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MEMORY CONTEXT MODELS
# ============================================================================

class MemoryContext(BaseModel):
    """Context for memory retrieval and injection."""
    task_id: str
    agent_name: str
    query: str
    max_memories: int = 10
    include_types: List[MemoryType] = Field(default_factory=list)
    exclude_types: List[MemoryType] = Field(default_factory=list)
    time_window_hours: Optional[int] = None
    importance_threshold: float = 0.5


class MemoryInjection(BaseModel):
    """Memory content injected into agent context."""
    memories: List[MemoryItem]
    total_tokens: int
    retrieval_query: str
    retrieval_time_ms: float
    context_metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MEMORY UTILITIES
# ============================================================================

def calculate_memory_importance(content: str, agent_name: str, 
                              memory_type: MemoryType, metadata: Dict[str, Any] = None) -> float:
    """Calculate importance score for a memory item."""
    base_importance = 1.0
    
    # Adjust based on memory type
    type_weights = {
        MemoryType.CONSTRAINT: 1.5,
        MemoryType.HOT_ISSUE: 1.8,
        MemoryType.DOCUMENT_CHUNK: 1.0,
        MemoryType.TEXT: 1.2,
        MemoryType.JSON: 1.1,
        MemoryType.KEY_VALUE: 1.0,
        MemoryType.VERSIONED_TEXT: 1.3
    }
    
    importance = base_importance * type_weights.get(memory_type, 1.0)
    
    # Adjust based on content length (longer content might be more important)
    content_length_factor = min(len(content) / 1000, 2.0)  # Cap at 2x
    importance *= (1.0 + content_length_factor * 0.2)
    
    # Adjust based on metadata
    if metadata:
        if metadata.get('user_flagged'):
            importance *= 1.5
        if metadata.get('error_related'):
            importance *= 1.3
        if metadata.get('success_related'):
            importance *= 1.2
    
    return min(importance, 10.0)  # Cap at 10.0


def create_memory_item(content: str, memory_type: MemoryType, agent_name: str,
                      metadata: Dict[str, Any] = None, importance: float = None) -> MemoryItem:
    """Create a new memory item with calculated importance."""
    if importance is None:
        importance = calculate_memory_importance(content, agent_name, memory_type, metadata)
    
    return MemoryItem(
        content=content,
        memory_type=memory_type,
        agent_name=agent_name,
        metadata=metadata or {},
        importance=importance
    ) 