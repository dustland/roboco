"""
Memory component for context and knowledge management.

This module provides the main Memory interface that agents use, backed by
intelligent memory backends (Mem0) for semantic search and advanced operations.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from ..memory import create_memory_backend, MemoryBackend, MemoryQuery, MemoryType
from ..config.models import MemoryConfig

logger = logging.getLogger(__name__)


@dataclass
class MemoryItem:
    """A single memory item - backward compatibility wrapper."""
    content: str
    agent_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    memory_id: str = field(default_factory=lambda: str(uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0  # 0.0 to 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "memory_id": self.memory_id,
            "metadata": self.metadata,
            "importance": self.importance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class Memory:
    """
    Memory component for individual agents.
    
    Provides a simple interface backed by intelligent memory backends
    for semantic search and advanced memory operations.
    """
    
    def __init__(self, agent: "Agent", config: Optional[MemoryConfig] = None):
        self.agent = agent
        self._backend: Optional[MemoryBackend] = None
        self._config = config
        
        # Memory configuration
        self.max_memories = 1000
        self.importance_threshold = 0.1
        
        # Backward compatibility - keep simple storage for fallback
        self.memories: List[MemoryItem] = []
        self._memory_index: Dict[str, MemoryItem] = {}
        
        logger.debug(f"Initialized memory for agent '{agent.name}'")
    
    async def _get_backend(self) -> MemoryBackend:
        """Get or create the memory backend."""
        if self._backend is None:
            try:
                self._backend = create_memory_backend(self._config)
            except Exception as e:
                logger.warning(f"Failed to create memory backend, using fallback: {e}")
                # Could implement a simple fallback backend here
                raise
        return self._backend
    
    def save(self, content: str, metadata: Optional[Dict[str, Any]] = None, importance: float = 1.0):
        """Save content to memory (sync wrapper)."""
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                task = asyncio.create_task(self.save_async(content, metadata, importance))
                # For now, we can't wait for it in sync context
                logger.warning("save() called in async context, use save_async() instead")
            else:
                loop.run_until_complete(self.save_async(content, metadata, importance))
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            # Fallback to simple storage
            self._save_fallback(content, metadata, importance)
    
    async def save_async(self, content: str, metadata: Optional[Dict[str, Any]] = None, importance: float = 1.0) -> str:
        """Save content to memory (async)."""
        try:
            backend = await self._get_backend()
            memory_id = await backend.add(
                content=content,
                memory_type=MemoryType.TEXT,  # Default to text
                agent_name=self.agent.name,
                metadata=metadata,
                importance=importance
            )
            logger.debug(f"Saved memory {memory_id} for {self.agent.name}: {content[:50]}...")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to save memory to backend: {e}")
            # Fallback to simple storage
            return self._save_fallback(content, metadata, importance)
    
    def _save_fallback(self, content: str, metadata: Optional[Dict[str, Any]] = None, importance: float = 1.0) -> str:
        """Fallback save to simple storage."""
        memory_item = MemoryItem(
            content=content,
            agent_name=self.agent.name,
            metadata=metadata or {},
            importance=importance
        )
        
        self.memories.append(memory_item)
        self._memory_index[memory_item.memory_id] = memory_item
        
        # Cleanup old memories if needed
        self._cleanup_memories()
        
        logger.debug(f"Saved memory (fallback) for {self.agent.name}: {content[:50]}...")
        return memory_item.memory_id
    
    def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search memories by content (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("search() called in async context, use search_async() instead")
                return self._search_fallback(query, limit)
            else:
                return loop.run_until_complete(self.search_async(query, limit))
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return self._search_fallback(query, limit)
    
    async def search_async(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search memories by content (async)."""
        try:
            backend = await self._get_backend()
            memory_query = MemoryQuery(
                query=query,
                agent_name=self.agent.name,
                limit=limit
            )
            
            result = await backend.search(memory_query)
            
            # Convert backend MemoryItems to local MemoryItems for compatibility
            return [self._convert_backend_item(item) for item in result.items]
            
        except Exception as e:
            logger.error(f"Failed to search memory in backend: {e}")
            return self._search_fallback(query, limit)
    
    def _search_fallback(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Fallback search using simple text matching."""
        query_lower = query.lower()
        
        matches = []
        for memory in self.memories:
            if query_lower in memory.content.lower():
                matches.append(memory)
        
        # Sort by importance and recency
        matches.sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
        
        return matches[:limit]
    
    def _convert_backend_item(self, backend_item) -> MemoryItem:
        """Convert backend MemoryItem to local MemoryItem."""
        return MemoryItem(
            content=backend_item.content,
            agent_name=backend_item.agent_name,
            timestamp=backend_item.timestamp,
            memory_id=backend_item.memory_id,
            metadata=backend_item.metadata,
            importance=backend_item.importance
        )
    
    def get_recent(self, limit: int = 10) -> List[MemoryItem]:
        """Get recent memories."""
        return sorted(self.memories, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def get_important(self, limit: int = 10) -> List[MemoryItem]:
        """Get most important memories."""
        return sorted(self.memories, key=lambda m: m.importance, reverse=True)[:limit]
    
    def get_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """Get memory by ID."""
        return self._memory_index.get(memory_id)
    
    def update_importance(self, memory_id: str, importance: float):
        """Update memory importance."""
        memory = self.get_by_id(memory_id)
        if memory:
            memory.importance = max(0.0, min(1.0, importance))
            logger.debug(f"Updated memory importance: {memory_id} -> {importance}")
    
    def delete(self, memory_id: str):
        """Delete a memory."""
        memory = self._memory_index.pop(memory_id, None)
        if memory:
            self.memories.remove(memory)
            logger.debug(f"Deleted memory: {memory_id}")
    
    def clear(self):
        """Clear all memories."""
        self.memories.clear()
        self._memory_index.clear()
        logger.debug(f"Cleared all memories for {self.agent.name}")
    
    def _cleanup_memories(self):
        """Clean up old or unimportant memories."""
        if len(self.memories) <= self.max_memories:
            return
        
        # Remove memories below importance threshold first
        low_importance = [m for m in self.memories if m.importance < self.importance_threshold]
        for memory in low_importance:
            self.delete(memory.memory_id)
        
        # If still too many, remove oldest
        if len(self.memories) > self.max_memories:
            sorted_memories = sorted(self.memories, key=lambda m: m.timestamp)
            excess_count = len(self.memories) - self.max_memories
            
            for memory in sorted_memories[:excess_count]:
                self.delete(memory.memory_id)
        
        logger.debug(f"Memory cleanup completed for {self.agent.name}")
    
    def get_context(self, query: str = "", max_items: int = 5) -> str:
        """Get relevant context for a query."""
        if query:
            relevant_memories = self.search(query, max_items)
        else:
            relevant_memories = self.get_recent(max_items)
        
        if not relevant_memories:
            return ""
        
        context_parts = []
        for memory in relevant_memories:
            context_parts.append(f"- {memory.content}")
        
        return "\n".join(context_parts)
    
    def save_conversation_summary(self, summary: str, participants: List[str]):
        """Save a conversation summary."""
        metadata = {
            "type": "conversation_summary",
            "participants": participants
        }
        self.save(summary, metadata, importance=0.8)
    
    def save_learning(self, learning: str, topic: str):
        """Save a learning or insight."""
        metadata = {
            "type": "learning",
            "topic": topic
        }
        self.save(learning, metadata, importance=0.9)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.memories:
            return {
                "total_memories": 0,
                "avg_importance": 0.0,
                "oldest_memory": None,
                "newest_memory": None
            }
        
        return {
            "total_memories": len(self.memories),
            "avg_importance": sum(m.importance for m in self.memories) / len(self.memories),
            "oldest_memory": min(self.memories, key=lambda m: m.timestamp).timestamp.isoformat(),
            "newest_memory": max(self.memories, key=lambda m: m.timestamp).timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent.name,
            "memories": [m.to_dict() for m in self.memories],
            "stats": self.get_stats()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], agent: "Agent") -> "Memory":
        """Create from dictionary."""
        memory = cls(agent)
        for memory_data in data.get("memories", []):
            memory_item = MemoryItem.from_dict(memory_data)
            memory.memories.append(memory_item)
            memory._memory_index[memory_item.memory_id] = memory_item
        return memory 