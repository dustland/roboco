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


@dataclass
class MemoryItem:
    """Individual memory item with metadata."""
    memory_id: str
    content: str
    agent_name: str
    timestamp: datetime
    memory_type: MemoryType
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0
    tags: List[str] = field(default_factory=list)
    source_event_id: Optional[str] = None
    is_active: bool = True
    
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
            "is_active": self.is_active
        }


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


@dataclass
class MemoryStats:
    """Memory backend statistics."""
    total_memories: int
    memory_types: Dict[str, int]
    agent_counts: Dict[str, int]
    storage_size_mb: float
    avg_query_time_ms: float
    last_updated: datetime 