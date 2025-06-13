"""
Memory management system using Mem0 for intelligent memory operations.
"""

import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from mem0 import Memory
from ..config.models import MemoryConfig


@dataclass
class MemoryEntry:
    """Represents a memory entry with metadata."""
    id: str
    content: str
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaskMemory:
    """
    Task-scoped memory operations using Mem0 backend.
    
    This class provides memory operations automatically scoped to a specific task,
    leveraging Mem0's intelligent memory extraction, semantic search, and graph-based storage.
    """

    def __init__(self, task_id: Optional[str] = None, config: Optional[MemoryConfig] = None):
        """Initialize task memory with Mem0 backend.
        
        Args:
            task_id: Optional task ID to scope all operations to
            config: Optional memory configuration
        """
        self.task_id = task_id
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

    def add(
        self,
        content: Union[str, List[Dict[str, str]]],
        agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a memory for this task.
        
        Args:
            content: Text content or conversation messages to store
            agent_id: Optional agent identifier  
            metadata: Optional metadata to associate with the memory
            
        Returns:
            Dict containing the result of the memory addition
        """
        try:
            # Prepare keyword arguments
            kwargs = {}
            if agent_id:
                kwargs["agent_id"] = agent_id
            if self.task_id:
                kwargs["run_id"] = self.task_id  # Mem0 still uses run_id internally
            if metadata:
                kwargs["metadata"] = metadata

            # Add memory using Mem0
            result = self._client.add(content, **kwargs)
            return result

        except Exception as e:
            return {"error": str(e), "success": False}

    def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories for this task using semantic similarity.
        
        Args:
            query: Search query
            agent_id: Optional agent identifier to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of relevant memories
        """
        try:
            # Prepare keyword arguments
            kwargs = {"limit": limit}
            if agent_id:
                kwargs["agent_id"] = agent_id
            if self.task_id:
                kwargs["run_id"] = self.task_id  # Mem0 still uses run_id internally

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
                        task_id=item.get("run_id"),  # Map run_id back to task_id
                        metadata=item.get("metadata", {}),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at")
                    )
                    memories.append(memory.to_dict())
            
            return memories

        except Exception as e:
            print(f"Error searching memories: {e}")
            return []

    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by ID.
        
        Args:
            memory_id: The ID of the memory to retrieve
            
        Returns:
            Memory entry if found, None otherwise
        """
        try:
            result = self._client.get(memory_id)
            if result:
                memory = MemoryEntry(
                    id=result.get("id", ""),
                    content=result.get("memory", ""),
                    user_id=result.get("user_id"),
                    agent_id=result.get("agent_id"),
                    task_id=result.get("run_id"),  # Map run_id back to task_id
                    metadata=result.get("metadata", {}),
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at")
                )
                return memory.to_dict()
            return None

        except Exception as e:
            print(f"Error getting memory {memory_id}: {e}")
            return None

    def get_all(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all memories for this task.
        
        Args:
            agent_id: Optional agent identifier to filter by
            limit: Maximum number of memories to return
            
        Returns:
            List of memory entries
        """
        try:
            # Prepare keyword arguments
            kwargs = {"limit": limit}
            if agent_id:
                kwargs["agent_id"] = agent_id
            if self.task_id:
                kwargs["run_id"] = self.task_id  # Mem0 still uses run_id internally

            # Get all memories using Mem0
            results = self._client.get_all(**kwargs)
            
            # Convert to our standard format
            memories = []
            if isinstance(results, list):
                for item in results:
                    memory = MemoryEntry(
                        id=item.get("id", ""),
                        content=item.get("memory", ""),
                        user_id=item.get("user_id"),
                        agent_id=item.get("agent_id"),
                        task_id=item.get("run_id"),  # Map run_id back to task_id
                        metadata=item.get("metadata", {}),
                        created_at=item.get("created_at"),
                        updated_at=item.get("updated_at")
                    )
                    memories.append(memory.to_dict())
            
            return memories

        except Exception as e:
            print(f"Error listing memories: {e}")
            return []

    def update(self, memory_id: str, content: str) -> Dict[str, Any]:
        """
        Update an existing memory.
        
        Args:
            memory_id: The ID of the memory to update
            content: New content for the memory
            
        Returns:
            Dict containing the result of the update
        """
        try:
            result = self._client.update(memory_id, content)
            return result

        except Exception as e:
            return {"error": str(e), "success": False}

    def delete(self, memory_id: str) -> Dict[str, Any]:
        """
        Delete a specific memory.
        
        Args:
            memory_id: The ID of the memory to delete
            
        Returns:
            Dict containing the result of the deletion
        """
        try:
            result = self._client.delete(memory_id)
            return result

        except Exception as e:
            return {"error": str(e), "success": False}

    def clear(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear all memories for this task.
        
        Args:
            agent_id: Optional agent identifier to filter by
            
        Returns:
            Dict containing the result of the operation
        """
        try:
            # Prepare keyword arguments
            kwargs = {}
            if agent_id:
                kwargs["agent_id"] = agent_id
            if self.task_id:
                kwargs["run_id"] = self.task_id  # Mem0 still uses run_id internally

            # Delete all memories using Mem0
            result = self._client.delete_all(**kwargs)
            return result

        except Exception as e:
            return {"error": str(e), "success": False}

    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """
        Get the history of changes for a specific memory.
        
        Args:
            memory_id: The ID of the memory
            
        Returns:
            List of history entries
        """
        try:
            result = self._client.history(memory_id)
            return result if result else []

        except Exception as e:
            print(f"Error getting memory history: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory system.
        
        Returns:
            Dict containing memory statistics
        """
        try:
            # Get all memories for this task to calculate stats
            all_memories = self.get_all()
            
            stats = {
                "total_memories": len(all_memories),
                "task_id": self.task_id,
                "agents": list(set(m.get("agent_id") for m in all_memories if m.get("agent_id"))),
                "memory_types": list(set(m.get("metadata", {}).get("type") for m in all_memories if m.get("metadata", {}).get("type")))
            }
            
            return stats

        except Exception as e:
            return {"error": str(e), "total_memories": 0}


class AgentMemory:
    """
    Agent-scoped memory operations.
    
    This class provides memory operations automatically scoped to a specific agent,
    optionally within a task context.
    """

    def __init__(self, agent_id: str, task_id: Optional[str] = None, config: Optional[MemoryConfig] = None):
        """Initialize agent memory.
        
        Args:
            agent_id: Agent identifier to scope operations to
            task_id: Optional task ID to further scope operations
            config: Optional memory configuration
        """
        self.agent_id = agent_id
        self.task_memory = TaskMemory(task_id=task_id, config=config)

    def add(
        self,
        content: Union[str, List[Dict[str, str]]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add a memory for this agent."""
        return self.task_memory.add(content=content, agent_id=self.agent_id, metadata=metadata)

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search memories for this agent."""
        return self.task_memory.search(query=query, agent_id=self.agent_id, limit=limit)

    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all memories for this agent."""
        return self.task_memory.get_all(agent_id=self.agent_id, limit=limit)

    def clear(self) -> Dict[str, Any]:
        """Clear all memories for this agent."""
        return self.task_memory.clear(agent_id=self.agent_id) 