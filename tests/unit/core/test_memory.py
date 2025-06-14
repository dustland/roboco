"""
Tests for the Memory class.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from roboco.core.memory import Memory, MemoryItem
from roboco.core.agent import Agent, AgentConfig


class TestMemoryItem:
    """Test MemoryItem class."""
    
    def test_memory_item_creation(self):
        """Test MemoryItem creation with default values."""
        item = MemoryItem(content="test content", agent_name="test_agent")
        
        assert item.content == "test content"
        assert item.agent_name == "test_agent"
        assert isinstance(item.timestamp, datetime)
        assert isinstance(item.memory_id, str)
        assert len(item.memory_id) > 0
        assert item.metadata == {}
        assert item.importance == 1.0
    
    def test_memory_item_creation_with_custom_values(self):
        """Test MemoryItem creation with custom values."""
        timestamp = datetime.now()
        metadata = {"key": "value", "type": "test"}
        
        item = MemoryItem(
            content="custom content",
            agent_name="custom_agent",
            timestamp=timestamp,
            memory_id="custom_id",
            metadata=metadata,
            importance=0.5
        )
        
        assert item.content == "custom content"
        assert item.agent_name == "custom_agent"
        assert item.timestamp == timestamp
        assert item.memory_id == "custom_id"
        assert item.metadata == metadata
        assert item.importance == 0.5
    
    def test_memory_item_to_dict(self):
        """Test MemoryItem to_dict conversion."""
        timestamp = datetime.now()
        item = MemoryItem(
            content="test content",
            agent_name="test_agent",
            timestamp=timestamp,
            memory_id="test_id",
            metadata={"key": "value"},
            importance=0.8
        )
        
        result = item.to_dict()
        
        assert result["content"] == "test content"
        assert result["agent_name"] == "test_agent"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["memory_id"] == "test_id"
        assert result["metadata"] == {"key": "value"}
        assert result["importance"] == 0.8
    
    def test_memory_item_from_dict(self):
        """Test MemoryItem from_dict creation."""
        timestamp = datetime.now()
        data = {
            "content": "test content",
            "agent_name": "test_agent",
            "timestamp": timestamp.isoformat(),
            "memory_id": "test_id",
            "metadata": {"key": "value"},
            "importance": 0.8
        }
        
        item = MemoryItem.from_dict(data)
        
        assert item.content == "test content"
        assert item.agent_name == "test_agent"
        assert item.timestamp == timestamp
        assert item.memory_id == "test_id"
        assert item.metadata == {"key": "value"}
        assert item.importance == 0.8
    
    def test_memory_item_from_dict_with_datetime_object(self):
        """Test MemoryItem from_dict with datetime object."""
        timestamp = datetime.now()
        data = {
            "content": "test content",
            "agent_name": "test_agent",
            "timestamp": timestamp,  # datetime object, not string
            "memory_id": "test_id"
        }
        
        item = MemoryItem.from_dict(data)
        assert item.timestamp == timestamp


class TestMemory:
    """Test Memory class."""
    
    def test_memory_initialization(self, mock_agent):
        """Test Memory initialization."""
        memory = Memory(mock_agent)
        
        assert memory.agent == mock_agent
        assert memory._backend is None
        assert memory._config is None
        assert memory.max_memories == 1000
        assert memory.importance_threshold == 0.1
        assert memory.memories == []
        assert memory._memory_index == {}
    
    def test_memory_initialization_with_config(self, mock_agent):
        """Test Memory initialization with config."""
        config = Mock()
        memory = Memory(mock_agent, config)
        
        assert memory._config == config
    
    def test_save_fallback(self, mock_agent):
        """Test save with fallback storage."""
        memory = Memory(mock_agent)
        
        memory_id = memory._save_fallback("test content", {"key": "value"}, 0.8)
        
        assert len(memory.memories) == 1
        assert memory.memories[0].content == "test content"
        assert memory.memories[0].agent_name == "test_agent"
        assert memory.memories[0].metadata == {"key": "value"}
        assert memory.memories[0].importance == 0.8
        assert memory_id in memory._memory_index
        assert memory._memory_index[memory_id] == memory.memories[0]
    
    def test_save_fallback_cleanup(self, mock_agent):
        """Test save fallback with memory cleanup."""
        memory = Memory(mock_agent)
        memory.max_memories = 2
        
        # Add memories beyond limit
        memory._save_fallback("content 1")
        memory._save_fallback("content 2")
        memory._save_fallback("content 3")  # Should trigger cleanup
        
        # Should keep only the most recent memories
        assert len(memory.memories) <= memory.max_memories
    
    @pytest.mark.asyncio
    async def test_save_async_with_backend(self, mock_agent):
        """Test async save with backend."""
        memory = Memory(mock_agent)
        
        # Mock backend
        mock_backend = AsyncMock()
        mock_backend.add = AsyncMock(return_value="backend_memory_id")
        
        with patch.object(memory, '_get_backend', return_value=mock_backend):
            memory_id = await memory.save_async("test content", {"key": "value"}, 0.8)
            
            assert memory_id == "backend_memory_id"
            mock_backend.add.assert_called_once()
            call_args = mock_backend.add.call_args
            assert call_args[1]["content"] == "test content"
            assert call_args[1]["agent_name"] == "test_agent"
            assert call_args[1]["metadata"] == {"key": "value"}
            assert call_args[1]["importance"] == 0.8
    
    @pytest.mark.asyncio
    async def test_save_async_backend_failure(self, mock_agent):
        """Test async save with backend failure (fallback)."""
        memory = Memory(mock_agent)
        
        with patch.object(memory, '_get_backend', side_effect=Exception("Backend error")), \
             patch.object(memory, '_save_fallback', return_value="fallback_id") as mock_fallback:
            
            memory_id = await memory.save_async("test content")
            
            assert memory_id == "fallback_id"
            mock_fallback.assert_called_once_with("test content", None, 1.0)
    
    def test_search_fallback(self, mock_agent):
        """Test search with fallback storage."""
        memory = Memory(mock_agent)
        
        # Add some test memories
        memory._save_fallback("This is about cats", importance=0.9)
        memory._save_fallback("This is about dogs", importance=0.7)
        memory._save_fallback("This is about birds", importance=0.8)
        memory._save_fallback("Something completely different", importance=0.6)
        
        # Search for "cats"
        results = memory._search_fallback("cats", limit=10)
        
        assert len(results) == 1
        assert results[0].content == "This is about cats"
        
        # Search for "about" (should match multiple)
        results = memory._search_fallback("about", limit=2)
        
        assert len(results) == 2
        # Should be sorted by importance and recency
        assert results[0].importance >= results[1].importance
    
    @pytest.mark.asyncio
    async def test_search_async_with_backend(self, mock_agent):
        """Test async search with backend."""
        memory = Memory(mock_agent)
        
        # Mock backend and result
        mock_result = Mock()
        mock_result.items = [
            Mock(content="backend result", agent_name="test_agent", timestamp=datetime.now(),
                 memory_id="backend_id", metadata={}, importance=1.0)
        ]
        
        mock_backend = AsyncMock()
        mock_backend.search = AsyncMock(return_value=mock_result)
        
        with patch.object(memory, '_get_backend', return_value=mock_backend):
            results = await memory.search_async("test query", limit=5)
            
            assert len(results) == 1
            assert results[0].content == "backend result"
            
            mock_backend.search.assert_called_once()
            query_arg = mock_backend.search.call_args[0][0]
            assert query_arg.query == "test query"
            assert query_arg.agent_name == "test_agent"
            assert query_arg.limit == 5
    
    @pytest.mark.asyncio
    async def test_search_async_backend_failure(self, mock_agent):
        """Test async search with backend failure (fallback)."""
        memory = Memory(mock_agent)
        
        with patch.object(memory, '_get_backend', side_effect=Exception("Backend error")), \
             patch.object(memory, '_search_fallback', return_value=[]) as mock_fallback:
            
            results = await memory.search_async("test query")
            
            assert results == []
            mock_fallback.assert_called_once_with("test query", 10)
    
    def test_get_recent(self, mock_agent):
        """Test getting recent memories."""
        memory = Memory(mock_agent)
        
        # Add memories with different timestamps
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now() - timedelta(minutes=30)
        
        memory.memories = [
            MemoryItem("old content", "test_agent", timestamp=old_time),
            MemoryItem("recent content", "test_agent", timestamp=recent_time),
            MemoryItem("newest content", "test_agent")  # Uses current time
        ]
        
        recent = memory.get_recent(limit=2)
        
        assert len(recent) == 2
        assert recent[0].content == "newest content"
        assert recent[1].content == "recent content"
    
    def test_get_important(self, mock_agent):
        """Test getting important memories."""
        memory = Memory(mock_agent)
        
        memory.memories = [
            MemoryItem("low importance", "test_agent", importance=0.3),
            MemoryItem("high importance", "test_agent", importance=0.9),
            MemoryItem("medium importance", "test_agent", importance=0.6)
        ]
        
        important = memory.get_important(limit=2)
        
        assert len(important) == 2
        assert important[0].content == "high importance"
        assert important[1].content == "medium importance"
    
    def test_get_by_id(self, mock_agent):
        """Test getting memory by ID."""
        memory = Memory(mock_agent)
        
        memory_id = memory._save_fallback("test content")
        
        result = memory.get_by_id(memory_id)
        assert result is not None
        assert result.content == "test content"
        
        # Test non-existent ID
        result = memory.get_by_id("non_existent_id")
        assert result is None
    
    def test_update_importance(self, mock_agent):
        """Test updating memory importance."""
        memory = Memory(mock_agent)
        
        memory_id = memory._save_fallback("test content", importance=0.5)
        
        memory.update_importance(memory_id, 0.9)
        
        item = memory.get_by_id(memory_id)
        assert item.importance == 0.9
    
    def test_delete(self, mock_agent):
        """Test deleting memory."""
        memory = Memory(mock_agent)
        
        memory_id = memory._save_fallback("test content")
        assert len(memory.memories) == 1
        assert memory_id in memory._memory_index
        
        memory.delete(memory_id)
        
        assert len(memory.memories) == 0
        assert memory_id not in memory._memory_index
    
    def test_clear(self, mock_agent):
        """Test clearing all memories."""
        memory = Memory(mock_agent)
        
        memory._save_fallback("content 1")
        memory._save_fallback("content 2")
        assert len(memory.memories) == 2
        
        memory.clear()
        
        assert len(memory.memories) == 0
        assert len(memory._memory_index) == 0
    
    def test_get_context(self, mock_agent):
        """Test getting context string."""
        memory = Memory(mock_agent)
        
        memory._save_fallback("Important information about cats")
        memory._save_fallback("Some details about dogs")
        
        context = memory.get_context("cats", max_items=1)
        
        assert "cats" in context.lower()
        assert "Important information about cats" in context
    
    def test_get_context_empty(self, mock_agent):
        """Test getting context when no memories exist."""
        memory = Memory(mock_agent)
        
        context = memory.get_context("anything")
        
        assert context == ""  # Empty string when no memories, not a message
    
    def test_save_conversation_summary(self, mock_agent):
        """Test saving conversation summary."""
        memory = Memory(mock_agent)
        
        memory.save_conversation_summary("Great discussion about AI", ["agent1", "agent2"])
        
        assert len(memory.memories) == 1
        saved_memory = memory.memories[0]
        assert "Great discussion about AI" in saved_memory.content
        assert saved_memory.metadata["type"] == "conversation_summary"
        assert saved_memory.metadata["participants"] == ["agent1", "agent2"]
    
    def test_save_learning(self, mock_agent):
        """Test saving learning."""
        memory = Memory(mock_agent)
        
        memory.save_learning("Learned about machine learning", "AI")
        
        assert len(memory.memories) == 1
        saved_memory = memory.memories[0]
        assert "Learned about machine learning" in saved_memory.content
        assert saved_memory.metadata["type"] == "learning"
        assert saved_memory.metadata["topic"] == "AI"
    
    def test_get_stats(self, mock_agent):
        """Test getting memory statistics."""
        memory = Memory(mock_agent)
        
        # Empty memory stats
        stats = memory.get_stats()
        assert stats["total_memories"] == 0
        assert stats["avg_importance"] == 0.0  # Changed from memory_types
        assert stats["oldest_memory"] is None
        assert stats["newest_memory"] is None
        
        # Add some memories
        memory._save_fallback("content 1", metadata={"type": "conversation"})
        memory._save_fallback("content 2", metadata={"type": "learning"})
        memory._save_fallback("content 3", metadata={"type": "conversation"})
        
        stats = memory.get_stats()
        assert stats["total_memories"] == 3
        assert stats["avg_importance"] > 0  # Changed from memory_types check
        assert stats["oldest_memory"] is not None
        assert stats["newest_memory"] is not None
    
    def test_to_dict(self, mock_agent):
        """Test converting memory to dictionary."""
        memory = Memory(mock_agent)
        
        memory._save_fallback("test content", {"key": "value"})
        
        result = memory.to_dict()
        
        assert result["agent_name"] == "test_agent"
        assert len(result["memories"]) == 1  # Changed from max_memories check
        assert result["memories"][0]["content"] == "test content"
        assert "stats" in result  # Added stats check
    
    def test_from_dict(self, mock_agent):
        """Test creating memory from dictionary."""
        data = {
            "agent_name": "test_agent",
            "memories": [
                {
                    "content": "test content",
                    "agent_name": "test_agent",
                    "timestamp": datetime.now().isoformat(),
                    "memory_id": "test_id",
                    "metadata": {"key": "value"},
                    "importance": 0.8
                }
            ]
        }
        
        memory = Memory.from_dict(data, mock_agent)
        
        assert memory.agent == mock_agent
        assert len(memory.memories) == 1  # Changed from max_memories check
        assert memory.memories[0].content == "test content"
        assert memory.memories[0].importance == 0.8 