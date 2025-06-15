"""
Memory component for context and knowledge management.

This module provides the main Memory interface that agents use, backed by
intelligent memory backends (Mem0) for semantic search and advanced operations.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime

from ..memory.backend import MemoryBackend
from ..memory.factory import create_memory_backend
from ..memory.types import MemoryType
# MemoryConfig imported locally to avoid circular imports
from ..utils.logger import get_logger
from ..utils.id import generate_short_id

logger = get_logger(__name__)


@dataclass
class MemoryItem:
    """Individual memory item."""
    content: str
    agent_name: str
    memory_id: str = field(default_factory=generate_short_id)
    timestamp: datetime = field(default_factory=datetime.now)
    memory_type: MemoryType = MemoryType.TEXT
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "memory_id": self.memory_id,
            "content": self.content,
            "agent_name": self.agent_name,
            "timestamp": self.timestamp.isoformat(),
            "memory_type": self.memory_type.value,
            "metadata": self.metadata,
            "importance": self.importance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryItem":
        """Create from dictionary."""
        return cls(
            memory_id=data["memory_id"],
            content=data["content"],
            agent_name=data["agent_name"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            memory_type=MemoryType(data["memory_type"]),
            metadata=data.get("metadata", {}),
            importance=data.get("importance", 1.0)
        )


class Memory:
    """
    Memory component for individual agents.
    
    Provides a simple interface backed by intelligent memory backends
    for semantic search and advanced memory operations.
    """
    
    def __init__(self, agent: "Agent", config = None):
        self.agent = agent
        self._backend: Optional[MemoryBackend] = None
        self._config = config
        
        logger.debug(f"Initialized memory for agent '{agent.name}'")
    
    async def _get_backend(self) -> MemoryBackend:
        """Get or create the memory backend."""
        if self._backend is None:
            self._backend = create_memory_backend(self._config)
        return self._backend
    
    async def save_async(self, content: str, metadata: Optional[Dict[str, Any]] = None, importance: float = 1.0) -> str:
        """Save content to memory."""
        backend = await self._get_backend()
        memory_id = await backend.add(
            content=content,
            memory_type=MemoryType.TEXT,
            agent_name=self.agent.name,
            metadata=metadata,
            importance=importance
        )
        logger.debug(f"Saved memory {memory_id} for {self.agent.name}: {content[:50]}...")
        return memory_id
    
    def save(self, content: str, metadata: Optional[Dict[str, Any]] = None, importance: float = 1.0) -> str:
        """Save content to memory (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("save() called in async context, use save_async() instead")
                # Create task but can't wait for it in sync context
                task = asyncio.create_task(self.save_async(content, metadata, importance))
                return "pending"  # Return placeholder
            else:
                return loop.run_until_complete(self.save_async(content, metadata, importance))
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
            raise
    
    async def search_async(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search memories by content."""
        backend = await self._get_backend()
        results = await backend.search(
            query=query,
            agent_name=self.agent.name,
            limit=limit
        )
        
        # Convert backend results to MemoryItem objects
        memory_items = []
        for result in results:
            memory_item = MemoryItem(
                memory_id=result.get("memory_id", generate_short_id()),
                content=result["content"],
                agent_name=self.agent.name,
                timestamp=datetime.fromisoformat(result.get("timestamp", datetime.now().isoformat())),
                memory_type=MemoryType(result.get("memory_type", MemoryType.TEXT.value)),
                metadata=result.get("metadata", {}),
                importance=result.get("importance", 1.0)
            )
            memory_items.append(memory_item)
        
        logger.debug(f"Found {len(memory_items)} memories for query: {query}")
        return memory_items
    
    def search(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """Search memories by content (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("search() called in async context, use search_async() instead")
                return []  # Return empty list in async context
            else:
                return loop.run_until_complete(self.search_async(query, limit))
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            raise
    
    async def get_async(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        backend = await self._get_backend()
        result = await backend.get(memory_id, self.agent.name)
        
        if result:
            return MemoryItem(
                memory_id=result["memory_id"],
                content=result["content"],
                agent_name=self.agent.name,
                timestamp=datetime.fromisoformat(result.get("timestamp", datetime.now().isoformat())),
                memory_type=MemoryType(result.get("memory_type", MemoryType.TEXT.value)),
                metadata=result.get("metadata", {}),
                importance=result.get("importance", 1.0)
            )
        return None
    
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("get() called in async context, use get_async() instead")
                return None
            else:
                return loop.run_until_complete(self.get_async(memory_id))
        except Exception as e:
            logger.error(f"Failed to get memory: {e}")
            raise
    
    async def delete_async(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        backend = await self._get_backend()
        success = await backend.delete(memory_id, self.agent.name)
        if success:
            logger.debug(f"Deleted memory {memory_id} for {self.agent.name}")
        return success
    
    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("delete() called in async context, use delete_async() instead")
                return False
            else:
                return loop.run_until_complete(self.delete_async(memory_id))
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            raise
    
    async def clear_async(self) -> bool:
        """Clear all memories for this agent."""
        backend = await self._get_backend()
        success = await backend.clear(self.agent.name)
        if success:
            logger.debug(f"Cleared all memories for {self.agent.name}")
        return success
    
    def clear(self) -> bool:
        """Clear all memories for this agent (sync wrapper)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("clear() called in async context, use clear_async() instead")
                return False
            else:
                return loop.run_until_complete(self.clear_async())
        except Exception as e:
            logger.error(f"Failed to clear memory: {e}")
            raise
    
 