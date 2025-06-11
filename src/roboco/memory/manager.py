"""
Memory management system using Mem0 for intelligent memory operations.
"""

import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json

try:
    from mem0 import Memory
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False

from ..config.models import MemoryConfig


@dataclass
class MemoryEntry:
    """Represents a memory entry with metadata."""
    id: str
    content: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    run_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MemoryManager:
    """
    Manages memory operations using Mem0 backend.
    
    This class provides a unified interface for memory operations while leveraging
    Mem0's intelligent memory extraction, semantic search, and graph-based storage.
    """

    def __init__(self, config: Optional[MemoryConfig] = None):
        """Initialize the memory manager with Mem0 backend."""
        if not MEM0_AVAILABLE:
            raise ImportError(
                "mem0ai is required for memory functionality. "
                "Install it with: pip install mem0ai"
            )
        
        self.config = config or MemoryConfig()
        self._client = None
        self._setup_mem0()

    def _setup_mem0(self):
        """Setup Mem0 client with configuration."""
        # Use configuration directly if provided, otherwise use defaults
        if hasattr(self.config, '__dict__'):
            # Handle our MemoryConfig dataclass
            mem0_config = {}
            
            if hasattr(self.config, 'vector_store') and self.config.vector_store:
                mem0_config["vector_store"] = self.config.vector_store
            if hasattr(self.config, 'llm') and self.config.llm:
                mem0_config["llm"] = self.config.llm
            if hasattr(self.config, 'embedder') and self.config.embedder:
                mem0_config["embedder"] = self.config.embedder
            if hasattr(self.config, 'graph_store') and self.config.graph_store:
                mem0_config["graph_store"] = self.config.graph_store
            if hasattr(self.config, 'version') and self.config.version:
                mem0_config["version"] = self.config.version
            if hasattr(self.config, 'custom_fact_extraction_prompt') and self.config.custom_fact_extraction_prompt:
                mem0_config["custom_fact_extraction_prompt"] = self.config.custom_fact_extraction_prompt
            if hasattr(self.config, 'history_db_path') and self.config.history_db_path:
                mem0_config["history_db_path"] = self.config.history_db_path
                
        elif isinstance(self.config, dict):
            # Handle dictionary configuration directly
            mem0_config = self.config
        else:
            # Default configuration
            mem0_config = {}

        # Set up defaults if nothing provided
        if not mem0_config:
            # Default to ChromaDB which comes with mem0ai and doesn't require external services
            mem0_config = {
                "vector_store": {
                    "provider": "chroma",
                    "config": {
                        "collection_name": "roboco_memories",
                        "path": "./workspace/memory_db"
                    }
                },
                "version": "v1.1"
            }
            
            # Add LLM config if OpenAI key is available
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                mem0_config["llm"] = {
                    "provider": "openai",
                    "config": {
                        "api_key": openai_api_key,
                        "model": "gpt-4o-mini",
                        "temperature": 0.1,
                        "max_tokens": 2048,
                    }
                }
                mem0_config["embedder"] = {
                    "provider": "openai",
                    "config": {
                        "api_key": openai_api_key,
                        "model": "text-embedding-3-small"
                    }
                }

        # Initialize Mem0 client
        try:
            if mem0_config:
                self._client = Memory.from_config(mem0_config)
            else:
                # Fallback to default configuration
                self._client = Memory()
        except Exception as e:
            print(f"Warning: Could not initialize Mem0 with config: {e}")
            # Try with minimal config
            try:
                minimal_config = {
                    "vector_store": {
                        "provider": "chroma",
                        "config": {
                            "collection_name": "roboco_memories",
                            "path": "./workspace/memory_db"
                        }
                    }
                }
                self._client = Memory.from_config(minimal_config)
            except Exception as e2:
                print(f"Warning: Could not initialize Mem0 with minimal config: {e2}")
                # Final fallback
                self._client = Memory()

    def add_memory(
        self,
        content: Union[str, List[Dict[str, str]]],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a memory using Mem0's intelligent extraction.
        
        Args:
            content: Text content or conversation messages to store
            user_id: Optional user identifier
            agent_id: Optional agent identifier  
            run_id: Optional session/run identifier
            metadata: Optional metadata to associate with the memory
            
        Returns:
            Dict containing the result of the memory addition
        """
        try:
            # Prepare keyword arguments
            kwargs = {}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if run_id:
                kwargs["run_id"] = run_id
            if metadata:
                kwargs["metadata"] = metadata

            # Add memory using Mem0
            result = self._client.add(content, **kwargs)
            return result

        except Exception as e:
            return {"error": str(e), "success": False}

    def search_memory(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic similarity.
        
        Args:
            query: Search query
            user_id: Optional user identifier to filter by
            agent_id: Optional agent identifier to filter by
            run_id: Optional session/run identifier to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of relevant memories
        """
        try:
            # Prepare keyword arguments
            kwargs = {"limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if run_id:
                kwargs["run_id"] = run_id

            # Search memories using Mem0
            results = self._client.search(query, **kwargs)
            
            # Convert to our standard format
            memories = []
            if isinstance(results, dict) and "results" in results:
                for item in results["results"]:
                    memory = MemoryEntry(
                        id=item.get("id", ""),
                        content=item.get("memory", ""),
                        user_id=item.get("user_id"),
                        agent_id=item.get("agent_id"),
                        run_id=item.get("run_id"),
                        metadata=item.get("metadata", {}),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at")
                    )
                    memories.append(memory.to_dict())
            
            return memories

        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: The memory identifier
            
        Returns:
            Memory entry or None if not found
        """
        try:
            # Mem0 doesn't have a direct get by ID method
            # We'll use get_all and filter
            all_memories = self._client.get_all(limit=1000)
            
            if isinstance(all_memories, dict) and "results" in all_memories:
                for item in all_memories["results"]:
                    if item.get("id") == memory_id:
                        memory = MemoryEntry(
                            id=item.get("id", ""),
                            content=item.get("memory", ""),
                            user_id=item.get("user_id"),
                            agent_id=item.get("agent_id"),
                            run_id=item.get("run_id"),
                            metadata=item.get("metadata", {}),
                            created_at=item.get("created_at"),
                            updated_at=item.get("updated_at")
                        )
                        return memory.to_dict()
            
            return None

        except Exception as e:
            print(f"Error getting memory {memory_id}: {e}")
            return None

    def list_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List memories with optional filtering.
        
        Args:
            user_id: Optional user identifier to filter by
            agent_id: Optional agent identifier to filter by
            run_id: Optional session/run identifier to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of memory entries
        """
        try:
            # Prepare keyword arguments
            kwargs = {"limit": limit}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if run_id:
                kwargs["run_id"] = run_id

            # Get memories using Mem0
            results = self._client.get_all(**kwargs)
            
            # Convert to our standard format
            memories = []
            if isinstance(results, dict) and "results" in results:
                for item in results["results"]:
                    memory = MemoryEntry(
                        id=item.get("id", ""),
                        content=item.get("memory", ""),
                        user_id=item.get("user_id"),
                        agent_id=item.get("agent_id"),
                        run_id=item.get("run_id"),
                        metadata=item.get("metadata", {}),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at")
                    )
                    memories.append(memory.to_dict())
            
            return memories

        except Exception as e:
            print(f"Error listing memories: {e}")
            return []

    def update_memory(
        self,
        memory_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Update a memory entry.
        
        Args:
            memory_id: The memory identifier
            content: New content for the memory
            
        Returns:
            Dict containing the result of the update
        """
        try:
            result = self._client.update(memory_id=memory_id, data=content)
            return result

        except Exception as e:
            return {"error": str(e), "success": False}

    def delete_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a specific memory.
        
        Args:
            memory_id: The memory identifier
            
        Returns:
            Dict containing the result of the deletion
        """
        try:
            result = self._client.delete(memory_id=memory_id)
            return {"success": True, "message": f"Memory {memory_id} deleted"}

        except Exception as e:
            return {"error": str(e), "success": False}

    def clear_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clear memories with optional filtering.
        
        Args:
            user_id: Optional user identifier to filter by
            agent_id: Optional agent identifier to filter by
            run_id: Optional session/run identifier to filter by
            
        Returns:
            Dict containing the result of the clearing operation
        """
        try:
            # Prepare keyword arguments
            kwargs = {}
            if user_id:
                kwargs["user_id"] = user_id
            if agent_id:
                kwargs["agent_id"] = agent_id
            if run_id:
                kwargs["run_id"] = run_id

            if kwargs:
                # Delete specific memories
                result = self._client.delete_all(**kwargs)
            else:
                # Reset all memories
                result = self._client.reset()
                
            return {"success": True, "message": "Memories cleared"}

        except Exception as e:
            return {"error": str(e), "success": False}

    def get_memory_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Get the history of changes for a memory.
        
        Args:
            memory_id: The memory identifier
            
        Returns:
            List of history entries
        """
        try:
            history = self._client.history(memory_id=memory_id)
            return history if isinstance(history, list) else []

        except Exception as e:
            print(f"Error getting memory history for {memory_id}: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dict containing memory statistics
        """
        try:
            # Get total count of memories
            all_memories = self._client.get_all(limit=10000)
            total_count = 0
            
            if isinstance(all_memories, dict) and "results" in all_memories:
                total_count = len(all_memories["results"])

            return {
                "total_memories": total_count,
                "backend": "mem0ai",
                "version": "v1.1"
            }

        except Exception as e:
            return {"error": str(e), "total_memories": 0}


# Backward compatibility aliases
class IntelligentChunker:
    """Deprecated: Chunking is now handled by Mem0 internally."""
    
    def __init__(self, *args, **kwargs):
        print("Warning: IntelligentChunker is deprecated. Mem0 handles chunking internally.")
    
    def chunk_text(self, text: str, metadata: Optional[Dict] = None) -> List[Dict]:
        return [{"text": text, "metadata": metadata or {}}]


class TokenAwareRetriever:
    """Deprecated: Retrieval is now handled by Mem0's semantic search."""
    
    def __init__(self, *args, **kwargs):
        print("Warning: TokenAwareRetriever is deprecated. Use MemoryManager.search_memory instead.")
    
    def retrieve(self, query: str, max_tokens: int = 1000) -> List[Dict]:
        return []


class MemoryBackend:
    """Deprecated: Storage is now handled by Mem0's backends."""
    
    def __init__(self, *args, **kwargs):
        print("Warning: MemoryBackend is deprecated. Mem0 handles storage internally.")
    
    def store(self, *args, **kwargs):
        pass
    
    def retrieve(self, *args, **kwargs):
        return [] 