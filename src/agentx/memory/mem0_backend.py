"""
Mem0 Backend Implementation

Intelligent memory backend using Mem0 for semantic search, vector storage,
and advanced memory operations.
"""

from ..utils.logger import get_logger
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from .backend import MemoryBackend
from .types import MemoryItem, MemoryQuery, MemorySearchResult, MemoryStats, MemoryType

logger = get_logger(__name__)


class Mem0Backend(MemoryBackend):
    """Mem0-powered memory backend with semantic search and intelligent storage."""
    
    def __init__(self, config):
        """
        Initialize Mem0 backend.
        
        Args:
            config: Memory configuration
        """
        self.config = config
        self._mem0_client = None
        self._initialized = False
        self._memory_cache: Dict[str, MemoryItem] = {}
        
    async def _ensure_initialized(self):
        """Ensure Mem0 client is initialized."""
        if self._initialized:
            return
            
        try:
            # Import mem0 here to avoid dependency issues if not installed
            from mem0 import Memory
            
            # Initialize Mem0 with configuration
            mem0_config = {
                "vector_store": self.config.vector_store,
                "llm": self.config.llm,
                "embedder": self.config.embedder,
                "version": self.config.version
            }
            
            if self.config.graph_store:
                mem0_config["graph_store"] = self.config.graph_store
                
            if self.config.custom_fact_extraction_prompt:
                mem0_config["custom_fact_extraction_prompt"] = self.config.custom_fact_extraction_prompt
                
            if self.config.history_db_path:
                mem0_config["history_db_path"] = self.config.history_db_path
            
            self._mem0_client = Memory.from_config(mem0_config)
            self._initialized = True
            
            logger.info("Mem0 backend initialized successfully")
            
        except ImportError:
            logger.error("mem0ai package not installed. Install with: pip install mem0ai")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Mem0 backend: {e}")
            raise
    
    async def add(
        self, 
        content: str, 
        memory_type: MemoryType,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None,
        importance: float = 1.0
    ) -> str:
        """Add content to Mem0 memory."""
        await self._ensure_initialized()
        
        # Prepare metadata for Mem0
        mem0_metadata = {
            "memory_type": memory_type.value,
            "agent_name": agent_name,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        try:
            # Add to Mem0 with user_id as agent_name for isolation
            result = self._mem0_client.add(
                messages=content,
                user_id=agent_name,
                metadata=mem0_metadata
            )
            
            # Mem0 returns a list of results, get the first memory ID
            if result and len(result) > 0:
                memory_id = result[0].get("id", result[0].get("memory_id"))
                logger.debug(f"Added memory {memory_id} for agent {agent_name}")
                return str(memory_id)
            else:
                raise ValueError("No memory ID returned from Mem0")
                
        except Exception as e:
            logger.error(f"Failed to add memory to Mem0: {e}")
            raise
    
    async def query(self, query: MemoryQuery) -> MemorySearchResult:
        """Query Mem0 for content retrieval with semantic search."""
        await self._ensure_initialized()
        
        start_time = time.time()
        
        try:
            # Build Mem0 search parameters
            search_params = {
                "query": query.query,
                "user_id": query.agent_name,
                "limit": query.limit
            }
            
            # Add filters if specified
            filters = {}
            if query.memory_type:
                filters["memory_type"] = query.memory_type.value
            if query.metadata_filter:
                filters.update(query.metadata_filter)
            if query.importance_threshold:
                filters["importance"] = {"$gte": query.importance_threshold}
                
            if filters:
                search_params["filters"] = filters
            
            # Search Mem0
            results = self._mem0_client.search(**search_params)
            
            # Convert Mem0 results to MemoryItems
            memory_items = []
            for result in results:
                memory_item = self._mem0_result_to_memory_item(result)
                if memory_item:
                    memory_items.append(memory_item)
            
            query_time = (time.time() - start_time) * 1000
            
            return MemorySearchResult(
                items=memory_items,
                total_count=len(memory_items),
                query_time_ms=query_time,
                has_more=len(memory_items) == query.limit
            )
            
        except Exception as e:
            logger.error(f"Failed to query Mem0: {e}")
            raise
    
    async def search(self, query: MemoryQuery) -> MemorySearchResult:
        """Search Mem0 for item discovery and filtering."""
        # For now, use the same implementation as query
        # In the future, this could return lighter metadata-only results
        return await self.query(query)
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Get a specific memory by ID."""
        await self._ensure_initialized()
        
        # Check cache first
        if memory_id in self._memory_cache:
            return self._memory_cache[memory_id]
        
        try:
            # Mem0 doesn't have direct get by ID, so we'll search
            results = self._mem0_client.search(
                query="*",
                user_id="*",
                limit=1000  # Get many to find the specific ID
            )
            
            for result in results:
                memory_item = self._mem0_result_to_memory_item(result)
                if memory_item and memory_item.memory_id == memory_id:
                    self._memory_cache[memory_id] = memory_item
                    return memory_item
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get memory {memory_id}: {e}")
            return None
    
    async def update(self, memory_id: str, **kwargs) -> bool:
        """Update memory metadata or content."""
        await self._ensure_initialized()
        
        try:
            # Mem0 doesn't support direct updates, so we need to handle this differently
            # For now, we'll track updates in metadata
            existing_memory = await self.get(memory_id)
            if not existing_memory:
                return False
            
            # Create a new memory with updated fields
            updated_metadata = existing_memory.metadata.copy()
            updated_metadata.update(kwargs)
            
            # For boolean fields like is_active, update the MemoryItem directly
            if 'is_active' in kwargs:
                existing_memory.is_active = kwargs['is_active']
                updated_metadata['is_active'] = kwargs['is_active']
            
            if 'resolved_by_event_id' in kwargs:
                updated_metadata['resolved_by_event_id'] = kwargs['resolved_by_event_id']
            
            if 'resolved_at' in kwargs:
                updated_metadata['resolved_at'] = kwargs['resolved_at']
            
            # Update the memory in our tracking
            self._memory_cache[memory_id] = existing_memory
            
            logger.debug(f"Updated memory {memory_id} with {len(kwargs)} fields")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update memory {memory_id}: {e}")
            return False
    
    async def delete(self, memory_id: str) -> bool:
        """Delete memory from Mem0."""
        await self._ensure_initialized()
        
        try:
            result = self._mem0_client.delete(memory_id)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete memory {memory_id} from Mem0: {e}")
            return False
    
    async def clear(self, agent_name: Optional[str] = None) -> int:
        """Clear memories from Mem0."""
        await self._ensure_initialized()
        
        try:
            if agent_name:
                # Clear memories for specific agent
                result = self._mem0_client.delete_all(user_id=agent_name)
            else:
                # Clear all memories (use with caution)
                result = self._mem0_client.reset()
            
            return result.get("deleted_count", 0) if isinstance(result, dict) else 0
            
        except Exception as e:
            logger.error(f"Failed to clear memory from Mem0: {e}")
            return 0
    
    async def count(
        self, 
        memory_type: Optional[MemoryType] = None,
        agent_name: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """Count memories in Mem0."""
        await self._ensure_initialized()
        
        try:
            # Build filters
            filters = {}
            if memory_type:
                filters["memory_type"] = memory_type.value
            if metadata_filter:
                filters.update(metadata_filter)
            
            # Search with large limit to count
            results = self._mem0_client.search(
                query="",  # Empty query to get all
                user_id=agent_name,
                filters=filters if filters else None,
                limit=10000  # Large limit for counting
            )
            
            return len(results)
            
        except Exception as e:
            logger.error(f"Failed to count memory in Mem0: {e}")
            return 0
    
    async def stats(self) -> MemoryStats:
        """Get memory statistics from Mem0."""
        await self._ensure_initialized()
        
        try:
            # Get all memories to compute stats
            all_memories = self._mem0_client.get_all()
            
            if not all_memories:
                return MemoryStats(
                    total_memories=0,
                    memories_by_type={},
                    memories_by_agent={},
                    avg_importance=0.0,
                    oldest_memory=None,
                    newest_memory=None
                )
            
            # Compute statistics
            total_memories = len(all_memories)
            memories_by_type = {}
            memories_by_agent = {}
            importance_sum = 0.0
            timestamps = []
            
            for memory in all_memories:
                metadata = memory.get("metadata", {})
                
                # Count by type
                memory_type = metadata.get("memory_type", "unknown")
                memories_by_type[memory_type] = memories_by_type.get(memory_type, 0) + 1
                
                # Count by agent
                agent_name = metadata.get("agent_name", "unknown")
                memories_by_agent[agent_name] = memories_by_agent.get(agent_name, 0) + 1
                
                # Sum importance
                importance = metadata.get("importance", 1.0)
                importance_sum += importance
                
                # Collect timestamps
                timestamp_str = metadata.get("timestamp")
                if timestamp_str:
                    try:
                        timestamps.append(datetime.fromisoformat(timestamp_str))
                    except:
                        pass
            
            avg_importance = importance_sum / total_memories if total_memories > 0 else 0.0
            oldest_memory = min(timestamps) if timestamps else None
            newest_memory = max(timestamps) if timestamps else None
            
            return MemoryStats(
                total_memories=total_memories,
                memories_by_type=memories_by_type,
                memories_by_agent=memories_by_agent,
                avg_importance=avg_importance,
                oldest_memory=oldest_memory,
                newest_memory=newest_memory
            )
            
        except Exception as e:
            logger.error(f"Failed to get stats from Mem0: {e}")
            # Return empty stats on error
            return MemoryStats(
                total_memories=0,
                memories_by_type={},
                memories_by_agent={},
                avg_importance=0.0,
                oldest_memory=None,
                newest_memory=None
            )
    
    async def health(self) -> Dict[str, Any]:
        """Check Mem0 backend health."""
        try:
            await self._ensure_initialized()
            
            # Try a simple operation to test connectivity
            test_result = self._mem0_client.search(query="health_check", limit=1)
            
            return {
                "status": "healthy",
                "backend": "mem0",
                "initialized": self._initialized,
                "config": {
                    "vector_store": self.config.vector_store.get("provider") if self.config.vector_store else None,
                    "llm": self.config.llm.get("provider") if self.config.llm else None,
                    "embedder": self.config.embedder.get("provider") if self.config.embedder else None
                }
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "mem0",
                "error": str(e),
                "initialized": self._initialized
            }
    
    def _memory_item_to_mem0_result(self, memory_item: MemoryItem) -> Dict[str, Any]:
        """Convert MemoryItem to Mem0 result format."""
        return {
            "id": memory_item.memory_id,
            "memory": memory_item.content,
            "user_id": memory_item.agent_name,
            "created_at": memory_item.timestamp.isoformat(),
            "metadata": {
                **memory_item.metadata,
                "memory_type": memory_item.memory_type.value,
                "importance": memory_item.importance,
                "tags": memory_item.tags,
                "source_event_id": memory_item.source_event_id,
                "is_active": memory_item.is_active
            }
        }

    def _mem0_result_to_memory_item(self, result: Dict[str, Any]) -> Optional[MemoryItem]:
        """Convert Mem0 search result to MemoryItem."""
        try:
            metadata = result.get("metadata", {})
            
            # Handle memory type
            memory_type_str = metadata.get("memory_type", MemoryType.TEXT.value)
            try:
                memory_type = MemoryType(memory_type_str)
            except ValueError:
                memory_type = MemoryType.TEXT
            
            # Parse timestamp
            timestamp_str = result.get("created_at", datetime.now().isoformat())
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except ValueError:
                timestamp = datetime.now()
            
            return MemoryItem(
                memory_id=str(result.get("id", generate_short_id())),
                content=result.get("memory", result.get("content", "")),
                agent_name=result.get("user_id", "unknown"),
                timestamp=timestamp,
                memory_type=memory_type,
                metadata=metadata,
                importance=metadata.get("importance", 1.0),
                tags=metadata.get("tags", []),
                source_event_id=metadata.get("source_event_id"),
                is_active=metadata.get("is_active", True)
            )
        except Exception as e:
            logger.error(f"Failed to convert Mem0 result to MemoryItem: {e}")
            return None 