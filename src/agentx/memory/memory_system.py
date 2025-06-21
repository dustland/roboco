"""
Memory System - Coordinated Memory Management

This module provides the main Memory System interface that coordinates:
- Memory backend for storage
- Synthesis engine for event-driven analysis
- Context retrieval for agent prompt enhancement
"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime
import logging

from .backend import MemoryBackend
from .synthesis_engine import MemorySynthesisEngine
from .types import MemoryItem, MemoryQuery, MemorySearchResult, MemoryType
from ..event.types import Event
from ..utils.logger import get_logger

# Import Brain at runtime to avoid circular dependency
if TYPE_CHECKING:
    from ..core.brain import Brain

logger = get_logger(__name__)


class MemorySystem:
    """
    Coordinated Memory System that integrates storage, synthesis, and retrieval.
    
    This is the main interface for the memory system that provides:
    - Event-driven memory synthesis
    - Context-aware memory retrieval
    - Specialized memory management (constraints, hot issues, document chunks)
    """
    
    def __init__(self, backend: MemoryBackend, synthesis_engine: MemorySynthesisEngine = None):
        self.backend = backend
        self.synthesis_engine = synthesis_engine or MemorySynthesisEngine(backend)
        self._initialized = False
        
        logger.info("MemorySystem initialized")
    
    async def initialize(self) -> None:
        """Initialize the memory system."""
        if self._initialized:
            return
        
        try:
            # Initialize backend if needed
            if hasattr(self.backend, 'initialize'):
                await self.backend.initialize()
            
            self._initialized = True
            logger.info("MemorySystem fully initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize MemorySystem: {e}")
            raise
    
    async def on_event(self, event: Event) -> None:
        """
        Handle events for memory synthesis.
        
        This is the main event handler that gets called by the event bus.
        """
        if not self._initialized:
            await self.initialize()
        
        if self.synthesis_engine:
            await self.synthesis_engine.on_event(event)
    
    async def get_relevant_context(self, last_user_message: str, agent_name: str = None) -> str:
        """
        Get memory-derived context for agent prompt injection.
        
        This implements the context retrieval pipeline from the architecture.
        """
        if not self._initialized:
            await self.initialize()
        
        if self.synthesis_engine:
            return await self.synthesis_engine.get_relevant_context(last_user_message, agent_name)
        else:
            # Fallback to basic backend search
            return await self._basic_context_retrieval(last_user_message, agent_name)
    
    async def _basic_context_retrieval(self, query: str, agent_name: str = None) -> str:
        """Basic context retrieval without synthesis engine."""
        try:
            # Search for relevant memories
            search_query = MemoryQuery(
                query=query,
                agent_name=agent_name,
                limit=5
            )
            
            results = await self.backend.search(search_query)
            
            if not results.items:
                return ""
            
            # Format basic context
            context_parts = ["CONTEXT:", "---"]
            
            for item in results.items:
                context_parts.append(f"- {item.content[:200]}...")
            
            context_parts.append("---")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Error in basic context retrieval: {e}")
            return ""
    
    # Delegate methods to backend
    async def add_memory(
        self,
        content: str,
        memory_type: MemoryType,
        agent_name: str,
        metadata: Dict[str, Any] = None,
        importance: float = 1.0
    ) -> str:
        """Add a memory to the system."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.add(
            content=content,
            memory_type=memory_type,
            agent_name=agent_name,
            metadata=metadata or {},
            importance=importance
        )
    
    async def search_memories(self, query: MemoryQuery) -> MemorySearchResult:
        """Search memories in the system."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.search(query)
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.get(memory_id)
    
    async def update_memory(self, memory_id: str, **kwargs) -> bool:
        """Update memory fields."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.update(memory_id, **kwargs)
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.delete(memory_id)
    
    # Specialized memory operations
    async def get_active_constraints(self) -> List[MemoryItem]:
        """Get all active constraint memories."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.get_active_constraints()
    
    async def get_active_hot_issues(self) -> List[MemoryItem]:
        """Get all active hot issue memories."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.get_active_hot_issues()
    
    async def search_documents(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Search document chunks for semantic similarity."""
        if not self._initialized:
            await self.initialize()
        
        return await self.backend.search_documents(query, top_k)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        if not self._initialized:
            await self.initialize()
        
        try:
            stats = await self.backend.stats()
            health = await self.backend.health()
            
            constraints = await self.get_active_constraints()
            hot_issues = await self.get_active_hot_issues()
            
            return {
                "initialized": self._initialized,
                "backend_stats": stats,
                "backend_health": health,
                "synthesis_engine": self.synthesis_engine is not None,
                "active_constraints": len(constraints),
                "active_hot_issues": len(hot_issues),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "initialized": self._initialized,
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }


# Convenience function for creating memory systems
def create_memory_system(backend: MemoryBackend, brain: Optional['Brain'] = None) -> MemorySystem:
    """Create a memory system with synthesis engine."""
    synthesis_engine = MemorySynthesisEngine(backend, brain)
    return MemorySystem(backend, synthesis_engine) 