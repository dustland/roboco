"""
Tests for memory backend interface and factory.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from roboco.memory.backend import MemoryBackend
from roboco.memory.types import MemoryType, MemoryItem, MemoryQuery, MemorySearchResult, MemoryStats
from roboco.memory.factory import create_memory_backend


class MockMemoryBackend(MemoryBackend):
    """Mock implementation of MemoryBackend for testing."""
    
    def __init__(self):
        self.memories = {}
        self.next_id = 1
    
    async def add(self, content, memory_type, agent_name, metadata=None, importance=1.0):
        memory_id = f"mem_{self.next_id}"
        self.next_id += 1
        
        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            agent_name=agent_name,
            memory_id=memory_id,
            metadata=metadata or {},
            importance=importance
        )
        
        self.memories[memory_id] = item
        return memory_id
    
    async def query(self, query):
        # Simple mock implementation
        matching_items = []
        for item in self.memories.values():
            if query.query.lower() in item.content.lower():
                if query.agent_name is None or item.agent_name == query.agent_name:
                    matching_items.append(item)
        
        return MemorySearchResult(
            items=matching_items[:query.limit],
            total_count=len(matching_items),
            query_time_ms=10.0
        )
    
    async def search(self, query):
        return await self.query(query)
    
    async def get(self, memory_id, version=None):
        return self.memories.get(memory_id)
    
    async def update(self, memory_id, content=None, metadata=None, importance=None):
        if memory_id not in self.memories:
            return False
        
        item = self.memories[memory_id]
        if content is not None:
            item.content = content
        if metadata is not None:
            item.metadata.update(metadata)
        if importance is not None:
            item.importance = importance
        
        return True
    
    async def delete(self, memory_id):
        if memory_id in self.memories:
            del self.memories[memory_id]
            return True
        return False
    
    async def clear(self, agent_name=None):
        if agent_name is None:
            count = len(self.memories)
            self.memories.clear()
            return count
        
        to_delete = [
            mid for mid, item in self.memories.items()
            if item.agent_name == agent_name
        ]
        
        for mid in to_delete:
            del self.memories[mid]
        
        return len(to_delete)
    
    async def count(self, memory_type=None, agent_name=None, metadata_filter=None):
        count = 0
        for item in self.memories.values():
            if memory_type and item.memory_type != memory_type:
                continue
            if agent_name and item.agent_name != agent_name:
                continue
            if metadata_filter:
                if not all(item.metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue
            count += 1
        return count
    
    async def stats(self):
        if not self.memories:
            return MemoryStats(
                total_memories=0,
                memories_by_type={},
                memories_by_agent={},
                avg_importance=0.0,
                oldest_memory=None,
                newest_memory=None
            )
        
        memories_by_type = {}
        memories_by_agent = {}
        total_importance = 0
        
        for item in self.memories.values():
            # Count by type
            type_str = item.memory_type.value
            memories_by_type[type_str] = memories_by_type.get(type_str, 0) + 1
            
            # Count by agent
            memories_by_agent[item.agent_name] = memories_by_agent.get(item.agent_name, 0) + 1
            
            # Sum importance
            total_importance += item.importance
        
        timestamps = [item.timestamp for item in self.memories.values()]
        
        return MemoryStats(
            total_memories=len(self.memories),
            memories_by_type=memories_by_type,
            memories_by_agent=memories_by_agent,
            avg_importance=total_importance / len(self.memories),
            oldest_memory=min(timestamps),
            newest_memory=max(timestamps)
        )
    
    async def health(self):
        return {
            "status": "healthy",
            "backend": "mock",
            "memory_count": len(self.memories)
        }


class TestMemoryBackend:
    """Test MemoryBackend interface through mock implementation."""
    
    @pytest.fixture
    def backend(self):
        """Create a mock backend for testing."""
        return MockMemoryBackend()
    
    @pytest.mark.asyncio
    async def test_add_memory(self, backend):
        """Test adding memory to backend."""
        memory_id = await backend.add(
            content="test content",
            memory_type=MemoryType.TEXT,
            agent_name="test_agent",
            metadata={"key": "value"},
            importance=0.8
        )
        
        assert isinstance(memory_id, str)
        assert len(memory_id) > 0
        
        # Verify memory was stored
        item = await backend.get(memory_id)
        assert item is not None
        assert item.content == "test content"
        assert item.memory_type == MemoryType.TEXT
        assert item.agent_name == "test_agent"
        assert item.metadata == {"key": "value"}
        assert item.importance == 0.8
    
    @pytest.mark.asyncio
    async def test_query_memory(self, backend):
        """Test querying memory from backend."""
        # Add some test memories
        await backend.add("cats are great", MemoryType.TEXT, "agent1")
        await backend.add("dogs are awesome", MemoryType.TEXT, "agent1")
        await backend.add("birds can fly", MemoryType.TEXT, "agent2")
        
        # Query for cats
        query = MemoryQuery(query="cats", agent_name="agent1", limit=10)
        result = await backend.query(query)
        
        assert isinstance(result, MemorySearchResult)
        assert len(result.items) == 1
        assert result.items[0].content == "cats are great"
        assert result.total_count == 1
        assert result.query_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_search_memory(self, backend):
        """Test searching memory from backend."""
        # Add test memories
        await backend.add("machine learning", MemoryType.TEXT, "agent1")
        await backend.add("deep learning", MemoryType.TEXT, "agent1")
        
        # Search for learning
        query = MemoryQuery(query="learning", limit=5)
        result = await backend.search(query)
        
        assert len(result.items) == 2
        assert all("learning" in item.content for item in result.items)
    
    @pytest.mark.asyncio
    async def test_get_memory(self, backend):
        """Test getting memory by ID."""
        memory_id = await backend.add("test content", MemoryType.TEXT, "agent1")
        
        item = await backend.get(memory_id)
        assert item is not None
        assert item.memory_id == memory_id
        assert item.content == "test content"
        
        # Test non-existent ID
        item = await backend.get("non_existent")
        assert item is None
    
    @pytest.mark.asyncio
    async def test_update_memory(self, backend):
        """Test updating memory."""
        memory_id = await backend.add("original content", MemoryType.TEXT, "agent1")
        
        # Update content
        success = await backend.update(memory_id, content="updated content")
        assert success is True
        
        item = await backend.get(memory_id)
        assert item.content == "updated content"
        
        # Update metadata
        success = await backend.update(memory_id, metadata={"updated": True})
        assert success is True
        
        item = await backend.get(memory_id)
        assert item.metadata["updated"] is True
        
        # Update importance
        success = await backend.update(memory_id, importance=0.5)
        assert success is True
        
        item = await backend.get(memory_id)
        assert item.importance == 0.5
        
        # Test non-existent ID
        success = await backend.update("non_existent", content="new")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, backend):
        """Test deleting memory."""
        memory_id = await backend.add("to be deleted", MemoryType.TEXT, "agent1")
        
        # Verify it exists
        item = await backend.get(memory_id)
        assert item is not None
        
        # Delete it
        success = await backend.delete(memory_id)
        assert success is True
        
        # Verify it's gone
        item = await backend.get(memory_id)
        assert item is None
        
        # Test deleting non-existent
        success = await backend.delete("non_existent")
        assert success is False
    
    @pytest.mark.asyncio
    async def test_clear_memory(self, backend):
        """Test clearing memories."""
        # Add memories for different agents
        await backend.add("agent1 memory 1", MemoryType.TEXT, "agent1")
        await backend.add("agent1 memory 2", MemoryType.TEXT, "agent1")
        await backend.add("agent2 memory 1", MemoryType.TEXT, "agent2")
        
        # Clear agent1 memories
        count = await backend.clear(agent_name="agent1")
        assert count == 2
        
        # Verify agent1 memories are gone
        query = MemoryQuery(query="", agent_name="agent1")
        result = await backend.search(query)
        assert len(result.items) == 0
        
        # Verify agent2 memory still exists
        query = MemoryQuery(query="", agent_name="agent2")
        result = await backend.search(query)
        assert len(result.items) == 1
        
        # Clear all remaining
        count = await backend.clear()
        assert count == 1
        
        # Verify all gone
        query = MemoryQuery(query="")
        result = await backend.search(query)
        assert len(result.items) == 0
    
    @pytest.mark.asyncio
    async def test_count_memory(self, backend):
        """Test counting memories."""
        # Add test memories
        await backend.add("text content", MemoryType.TEXT, "agent1", {"type": "note"})
        await backend.add("json content", MemoryType.JSON, "agent1", {"type": "data"})
        await backend.add("more text", MemoryType.TEXT, "agent2", {"type": "note"})
        
        # Count all
        count = await backend.count()
        assert count == 3
        
        # Count by type
        count = await backend.count(memory_type=MemoryType.TEXT)
        assert count == 2
        
        # Count by agent
        count = await backend.count(agent_name="agent1")
        assert count == 2
        
        # Count by metadata
        count = await backend.count(metadata_filter={"type": "note"})
        assert count == 2
        
        # Count with multiple filters
        count = await backend.count(memory_type=MemoryType.TEXT, agent_name="agent1")
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_stats(self, backend):
        """Test getting memory statistics."""
        # Test empty stats
        stats = await backend.stats()
        assert stats.total_memories == 0
        assert stats.memories_by_type == {}
        assert stats.memories_by_agent == {}
        assert stats.avg_importance == 0.0
        assert stats.oldest_memory is None
        assert stats.newest_memory is None
        
        # Add some memories
        await backend.add("text 1", MemoryType.TEXT, "agent1", importance=0.8)
        await backend.add("json 1", MemoryType.JSON, "agent1", importance=0.6)
        await backend.add("text 2", MemoryType.TEXT, "agent2", importance=1.0)
        
        stats = await backend.stats()
        assert stats.total_memories == 3
        assert stats.memories_by_type == {"text": 2, "json": 1}
        assert stats.memories_by_agent == {"agent1": 2, "agent2": 1}
        assert stats.avg_importance == (0.8 + 0.6 + 1.0) / 3
        assert stats.oldest_memory is not None
        assert stats.newest_memory is not None
    
    @pytest.mark.asyncio
    async def test_health(self, backend):
        """Test health check."""
        health = await backend.health()
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] == "healthy"


class TestMemoryFactory:
    """Test memory backend factory."""
    
    def test_create_memory_backend_none_config(self):
        """Test creating backend with None config."""
        with patch('roboco.memory.factory.logger') as mock_logger:
            backend = create_memory_backend(None)
            assert backend is None
            mock_logger.warning.assert_called_once()
    
    def test_create_memory_backend_invalid_config(self):
        """Test creating backend with invalid config."""
        invalid_config = Mock()
        invalid_config.backend_type = "invalid_backend"
        
        with patch('roboco.memory.factory.logger') as mock_logger:
            backend = create_memory_backend(invalid_config)
            assert backend is None
            mock_logger.error.assert_called_once()
    
    @patch('roboco.memory.factory.Mem0Backend')
    def test_create_memory_backend_mem0(self, mock_mem0_class):
        """Test creating Mem0 backend."""
        mock_config = Mock()
        mock_config.backend_type = "mem0"
        mock_config.mem0_config = {"api_key": "test"}
        
        mock_backend = Mock()
        mock_mem0_class.return_value = mock_backend
        
        backend = create_memory_backend(mock_config)
        
        assert backend == mock_backend
        mock_mem0_class.assert_called_once_with(mock_config.mem0_config)
    
    @patch('roboco.memory.factory.Mem0Backend')
    def test_create_memory_backend_mem0_error(self, mock_mem0_class):
        """Test creating Mem0 backend with error."""
        mock_config = Mock()
        mock_config.backend_type = "mem0"
        mock_config.mem0_config = {"api_key": "test"}
        
        mock_mem0_class.side_effect = Exception("Connection failed")
        
        with patch('roboco.memory.factory.logger') as mock_logger:
            backend = create_memory_backend(mock_config)
            assert backend is None
            mock_logger.error.assert_called_once() 