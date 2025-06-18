"""
Memory Backend Interface

Abstract base class defining the contract for memory backend implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from .types import MemoryItem, MemoryQuery, MemorySearchResult, MemoryStats, MemoryType


class MemoryBackend(ABC):
    """
    Abstract interface for memory storage backends.
    
    Provides a clean interface for storing and retrieving memories,
    with support for specialized memory types (constraints, hot issues, document chunks).
    """
    
    @abstractmethod
    async def add(
        self,
        content: str,
        memory_type: MemoryType,
        agent_name: str,
        metadata: Dict[str, Any] = None,
        importance: float = 1.0
    ) -> str:
        """
        Add a memory to the backend.
        
        Args:
            content: Memory content
            memory_type: Type of memory (text, constraint, hot_issue, etc.)
            agent_name: Name of the agent creating the memory
            metadata: Additional metadata
            importance: Importance score (0.0 to 3.0)
            
        Returns:
            Memory ID
        """
        pass
    
    @abstractmethod
    async def search(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Search memories using semantic similarity and filters.
        
        Args:
            query: Search query with filters and parameters
            
        Returns:
            Search results with relevant memories
        """
        pass
    
    @abstractmethod
    async def query(self, query: MemoryQuery) -> MemorySearchResult:
        """Alias for search method for backward compatibility."""
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            Memory item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, **kwargs) -> bool:
        """
        Update memory metadata or content.
        
        Args:
            memory_id: Memory identifier
            **kwargs: Fields to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self, agent_name: str = None) -> int:
        """
        Clear memories, optionally filtered by agent.
        
        Args:
            agent_name: Agent name filter (None to clear all)
            
        Returns:
            Number of memories cleared
        """
        pass
    
    @abstractmethod
    async def count(self, **filters) -> int:
        """
        Count memories with optional filters.
        
        Args:
            **filters: Filter criteria
            
        Returns:
            Number of matching memories
        """
        pass
    
    @abstractmethod
    async def stats(self) -> MemoryStats:
        """
        Get memory backend statistics.
        
        Returns:
            Statistics about the memory backend
        """
        pass
    
    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """
        Get backend health status.
        
        Returns:
            Health status information
        """
        pass

    # Specialized methods for synthesis engine support
    async def get_active_constraints(self) -> List[MemoryItem]:
        """Get all active constraint memories."""
        query = MemoryQuery(
            query="*",
            memory_type=MemoryType.CONSTRAINT,
            metadata_filter={"is_active": True},
            limit=50
        )
        results = await self.search(query)
        return [item for item in results.items if item.is_active]

    async def get_active_hot_issues(self) -> List[MemoryItem]:
        """Get all active hot issue memories."""
        query = MemoryQuery(
            query="*",
            memory_type=MemoryType.HOT_ISSUE,
            metadata_filter={"is_active": True},
            limit=50
        )
        results = await self.search(query)
        return [item for item in results.items if item.is_active]

    async def get_active_rules(self) -> List[MemoryItem]:
        """Get all active constraints and hot issues."""
        constraints = await self.get_active_constraints()
        hot_issues = await self.get_active_hot_issues()
        return constraints + hot_issues

    async def search_documents(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Search document chunks for semantic similarity."""
        search_query = MemoryQuery(
            query=query,
            memory_type=MemoryType.DOCUMENT_CHUNK,
            limit=top_k
        )
        results = await self.search(search_query)
        return results.items

    async def save_memories(self, memories: List[Dict[str, Any]]) -> List[str]:
        """
        Save multiple memories in batch.
        
        Args:
            memories: List of memory dictionaries
            
        Returns:
            List of memory IDs
        """
        memory_ids = []
        for memory_data in memories:
            memory_id = await self.add(
                content=memory_data.get("content", ""),
                memory_type=MemoryType(memory_data.get("memory_type", MemoryType.TEXT.value)),
                agent_name=memory_data.get("agent_name", "system"),
                metadata=memory_data.get("metadata", {}),
                importance=memory_data.get("importance", 1.0)
            )
            memory_ids.append(memory_id)
        return memory_ids 