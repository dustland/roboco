"""
Memory Backend Interface

Abstract base class defining the contract for memory backend implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .types import MemoryItem, MemoryQuery, MemorySearchResult, MemoryStats, MemoryType


class MemoryBackend(ABC):
    """Abstract base class for memory backend implementations."""
    
    @abstractmethod
    async def add(
        self, 
        content: str, 
        memory_type: MemoryType,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0
    ) -> str:
        """
        Add content to memory.
        
        Args:
            content: The content to store
            memory_type: Type of memory content
            agent_name: Name of the agent adding the memory
            metadata: Optional metadata
            importance: Importance score (0.0-1.0)
            
        Returns:
            Memory ID of the stored item
        """
        pass
    
    @abstractmethod
    async def query(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Query memory for content retrieval with token limits.
        
        Args:
            query: Query parameters
            
        Returns:
            Search results with actual content
        """
        pass
    
    @abstractmethod
    async def search(self, query: MemoryQuery) -> MemorySearchResult:
        """
        Search memory for item discovery and filtering.
        
        Args:
            query: Query parameters
            
        Returns:
            Search results with metadata and references
        """
        pass
    
    @abstractmethod
    async def get(self, memory_id: str, version: Optional[int] = None) -> Optional[MemoryItem]:
        """
        Get memory by ID.
        
        Args:
            memory_id: Memory identifier
            version: Optional version number for versioned content
            
        Returns:
            Memory item if found
        """
        pass
    
    @abstractmethod
    async def update(
        self, 
        memory_id: str, 
        content: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        importance: Optional[float] = None
    ) -> bool:
        """
        Update existing memory.
        
        Args:
            memory_id: Memory identifier
            content: New content (optional)
            metadata: New metadata (optional)
            importance: New importance score (optional)
            
        Returns:
            True if updated successfully
        """
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """
        Delete memory by ID.
        
        Args:
            memory_id: Memory identifier
            
        Returns:
            True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def clear(self, agent_name: Optional[str] = None) -> int:
        """
        Clear memories.
        
        Args:
            agent_name: If provided, clear only memories for this agent
            
        Returns:
            Number of memories cleared
        """
        pass
    
    @abstractmethod
    async def count(
        self, 
        memory_type: Optional[MemoryType] = None,
        agent_name: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count memories matching criteria.
        
        Args:
            memory_type: Filter by memory type
            agent_name: Filter by agent name
            metadata_filter: Filter by metadata
            
        Returns:
            Count of matching memories
        """
        pass
    
    @abstractmethod
    async def stats(self) -> MemoryStats:
        """
        Get memory system statistics.
        
        Returns:
            Memory statistics
        """
        pass
    
    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """
        Check backend health and connectivity.
        
        Returns:
            Health status information
        """
        pass 