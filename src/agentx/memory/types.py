"""
Memory System Types

Data models and types for the memory backend system.
"""

from typing import Dict, List, Optional, Any, Union, Literal, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
try:
    from ..utils.id import generate_short_id
except ImportError:
    # Fallback if utils.id is not available
    import uuid
    def generate_short_id():
        return str(uuid.uuid4())[:8]


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


# Pydantic models for synthesis engine (as specified in architecture doc)
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
    

class HotIssue(Memory):
    """Memory representing active problems that need attention."""
    type: Literal["HOT_ISSUE"] = "HOT_ISSUE"
    # e.g., "Unit test 'test_payment_flow' is failing"
    resolved_by_event_id: Optional[UUID] = None


class DocumentChunk(Memory):
    """Memory representing a chunk of document content for semantic search."""
    type: Literal["DOCUMENT_CHUNK"] = "DOCUMENT_CHUNK"
    source_file_path: str
    chunk_index: int = 0
    # e.g., A chunk of text from a file


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


@dataclass
class MemorySearchResult:
    """Result from memory search operations."""
    items: List[MemoryItem]
    total_count: int
    query_time_ms: float
    has_more: bool = False
    query_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "has_more": self.has_more,
            "query_metadata": self.query_metadata
        }


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_memories": self.total_memories,
            "memories_by_type": self.memories_by_type,
            "memories_by_agent": self.memories_by_agent,
            "avg_importance": self.avg_importance,
            "oldest_memory": self.oldest_memory.isoformat() if self.oldest_memory else None,
            "newest_memory": self.newest_memory.isoformat() if self.newest_memory else None,
            "storage_size_mb": self.storage_size_mb
        } 