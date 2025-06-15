"""
Memory System Types

Data models and types for the memory backend system.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from ..utils.id import generate_short_id


class MemoryType(str, Enum):
    """Types of memory content."""
    TEXT = "text"
    JSON = "json"
    KEY_VALUE = "key_value"
    VERSIONED_TEXT = "versioned_text"


@dataclass
class MemoryItem:
    """A single memory item with rich metadata."""
    content: str
    memory_type: MemoryType
    agent_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    memory_id: str = field(default_factory=generate_short_id)
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # 0.0 to 1.0
    version: Optional[int] = None
    parent_id: Optional[str] = None  # For versioned content
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "memory_type": self.memory_type.value,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "memory_id": self.memory_id,
            "metadata": self.metadata,
            "importance": self.importance,
            "version": self.version,
            "parent_id": self.parent_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if "memory_type" in data and isinstance(data["memory_type"], str):
            data["memory_type"] = MemoryType(data["memory_type"])
        return cls(**data)


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
    time_range: Optional[tuple[datetime, datetime]] = None
    include_metadata: bool = True
    exclude_used_sources: bool = False


@dataclass 
class MemorySearchResult:
    """Result from memory search operations."""
    items: List[MemoryItem]
    total_count: int
    query_time_ms: float
    has_more: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "total_count": self.total_count,
            "query_time_ms": self.query_time_ms,
            "has_more": self.has_more
        }


@dataclass
class MemoryStats:
    """Memory system statistics."""
    total_memories: int
    memories_by_type: Dict[str, int]
    memories_by_agent: Dict[str, int]
    avg_importance: float
    oldest_memory: Optional[datetime]
    newest_memory: Optional[datetime]
    storage_size_mb: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_memories": self.total_memories,
            "memories_by_type": self.memories_by_type,
            "memories_by_agent": self.memories_by_agent,
            "avg_importance": self.avg_importance,
            "oldest_memory": self.oldest_memory.isoformat() if self.oldest_memory else None,
            "newest_memory": self.newest_memory.isoformat() if self.newest_memory else None,
            "storage_size_mb": self.storage_size_mb
        } 