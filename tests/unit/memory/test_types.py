"""
Tests for memory types and data structures.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from roboco.memory.types import (
    MemoryType, MemoryItem, MemoryQuery, MemorySearchResult, MemoryStats
)


class TestMemoryType:
    """Test MemoryType enum."""
    
    def test_memory_type_values(self):
        """Test MemoryType enum values."""
        assert MemoryType.TEXT.value == "text"
        assert MemoryType.JSON.value == "json"
        assert MemoryType.KEY_VALUE.value == "key_value"
        assert MemoryType.VERSIONED_TEXT.value == "versioned_text"
    
    def test_memory_type_string_behavior(self):
        """Test MemoryType string behavior."""
        assert str(MemoryType.TEXT) == "text"
        assert MemoryType.TEXT == "text"
        assert MemoryType("text") == MemoryType.TEXT


class TestMemoryItem:
    """Test MemoryItem class."""
    
    def test_memory_item_creation_minimal(self):
        """Test MemoryItem creation with minimal parameters."""
        item = MemoryItem(
            content="test content",
            memory_type=MemoryType.TEXT,
            agent_name="test_agent"
        )
        
        assert item.content == "test content"
        assert item.memory_type == MemoryType.TEXT
        assert item.agent_name == "test_agent"
        assert isinstance(item.timestamp, datetime)
        assert isinstance(item.memory_id, str)
        assert len(item.memory_id) > 0
        assert item.metadata == {}
        assert item.importance == 1.0
        assert item.version is None
        assert item.parent_id is None
    
    def test_memory_item_creation_full(self):
        """Test MemoryItem creation with all parameters."""
        timestamp = datetime.now()
        metadata = {"key": "value", "type": "test"}
        
        item = MemoryItem(
            content="full content",
            memory_type=MemoryType.JSON,
            agent_name="full_agent",
            timestamp=timestamp,
            memory_id="custom_id",
            metadata=metadata,
            importance=0.8,
            version=2,
            parent_id="parent_123"
        )
        
        assert item.content == "full content"
        assert item.memory_type == MemoryType.JSON
        assert item.agent_name == "full_agent"
        assert item.timestamp == timestamp
        assert item.memory_id == "custom_id"
        assert item.metadata == metadata
        assert item.importance == 0.8
        assert item.version == 2
        assert item.parent_id == "parent_123"
    
    def test_memory_item_to_dict(self):
        """Test MemoryItem to_dict conversion."""
        timestamp = datetime.now()
        item = MemoryItem(
            content="test content",
            memory_type=MemoryType.TEXT,
            agent_name="test_agent",
            timestamp=timestamp,
            memory_id="test_id",
            metadata={"key": "value"},
            importance=0.7,
            version=1,
            parent_id="parent_id"
        )
        
        result = item.to_dict()
        
        assert result["content"] == "test content"
        assert result["memory_type"] == "text"
        assert result["agent_name"] == "test_agent"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["memory_id"] == "test_id"
        assert result["metadata"] == {"key": "value"}
        assert result["importance"] == 0.7
        assert result["version"] == 1
        assert result["parent_id"] == "parent_id"
    
    def test_memory_item_from_dict(self):
        """Test MemoryItem from_dict creation."""
        timestamp = datetime.now()
        data = {
            "content": "test content",
            "memory_type": "json",
            "agent_name": "test_agent",
            "timestamp": timestamp.isoformat(),
            "memory_id": "test_id",
            "metadata": {"key": "value"},
            "importance": 0.7,
            "version": 1,
            "parent_id": "parent_id"
        }
        
        item = MemoryItem.from_dict(data)
        
        assert item.content == "test content"
        assert item.memory_type == MemoryType.JSON
        assert item.agent_name == "test_agent"
        assert item.timestamp == timestamp
        assert item.memory_id == "test_id"
        assert item.metadata == {"key": "value"}
        assert item.importance == 0.7
        assert item.version == 1
        assert item.parent_id == "parent_id"
    
    def test_memory_item_from_dict_with_datetime_object(self):
        """Test MemoryItem from_dict with datetime object."""
        timestamp = datetime.now()
        data = {
            "content": "test content",
            "memory_type": MemoryType.TEXT,  # Enum object
            "agent_name": "test_agent",
            "timestamp": timestamp,  # datetime object
            "memory_id": "test_id"
        }
        
        item = MemoryItem.from_dict(data)
        assert item.timestamp == timestamp
        assert item.memory_type == MemoryType.TEXT


class TestMemoryQuery:
    """Test MemoryQuery class."""
    
    def test_memory_query_minimal(self):
        """Test MemoryQuery with minimal parameters."""
        query = MemoryQuery(query="test query")
        
        assert query.query == "test query"
        assert query.memory_type is None
        assert query.agent_name is None
        assert query.max_tokens is None
        assert query.limit == 10
        assert query.metadata_filter is None
        assert query.importance_threshold is None
        assert query.time_range is None
        assert query.include_metadata is True
        assert query.exclude_used_sources is False
    
    def test_memory_query_full(self):
        """Test MemoryQuery with all parameters."""
        start_time = datetime.now() - timedelta(days=1)
        end_time = datetime.now()
        metadata_filter = {"type": "conversation"}
        
        query = MemoryQuery(
            query="complex query",
            memory_type=MemoryType.TEXT,
            agent_name="test_agent",
            max_tokens=1000,
            limit=20,
            metadata_filter=metadata_filter,
            importance_threshold=0.5,
            time_range=(start_time, end_time),
            include_metadata=False,
            exclude_used_sources=True
        )
        
        assert query.query == "complex query"
        assert query.memory_type == MemoryType.TEXT
        assert query.agent_name == "test_agent"
        assert query.max_tokens == 1000
        assert query.limit == 20
        assert query.metadata_filter == metadata_filter
        assert query.importance_threshold == 0.5
        assert query.time_range == (start_time, end_time)
        assert query.include_metadata is False
        assert query.exclude_used_sources is True


class TestMemorySearchResult:
    """Test MemorySearchResult class."""
    
    def test_memory_search_result_creation(self):
        """Test MemorySearchResult creation."""
        items = [
            MemoryItem("content1", MemoryType.TEXT, "agent1"),
            MemoryItem("content2", MemoryType.JSON, "agent2")
        ]
        
        result = MemorySearchResult(
            items=items,
            total_count=2,
            query_time_ms=150.5,
            has_more=True
        )
        
        assert result.items == items
        assert result.total_count == 2
        assert result.query_time_ms == 150.5
        assert result.has_more is True
    
    def test_memory_search_result_defaults(self):
        """Test MemorySearchResult with default values."""
        result = MemorySearchResult(
            items=[],
            total_count=0,
            query_time_ms=50.0
        )
        
        assert result.items == []
        assert result.total_count == 0
        assert result.query_time_ms == 50.0
        assert result.has_more is False  # Default value
    
    def test_memory_search_result_to_dict(self):
        """Test MemorySearchResult to_dict conversion."""
        items = [
            MemoryItem("content1", MemoryType.TEXT, "agent1"),
            MemoryItem("content2", MemoryType.JSON, "agent2")
        ]
        
        result = MemorySearchResult(
            items=items,
            total_count=2,
            query_time_ms=150.5,
            has_more=True
        )
        
        dict_result = result.to_dict()
        
        assert len(dict_result["items"]) == 2
        assert dict_result["total_count"] == 2
        assert dict_result["query_time_ms"] == 150.5
        assert dict_result["has_more"] is True
        
        # Check that items are properly converted
        assert dict_result["items"][0]["content"] == "content1"
        assert dict_result["items"][0]["memory_type"] == "text"
        assert dict_result["items"][1]["content"] == "content2"
        assert dict_result["items"][1]["memory_type"] == "json"


class TestMemoryStats:
    """Test MemoryStats class."""
    
    def test_memory_stats_creation(self):
        """Test MemoryStats creation."""
        oldest = datetime.now() - timedelta(days=30)
        newest = datetime.now()
        
        stats = MemoryStats(
            total_memories=100,
            memories_by_type={"text": 80, "json": 20},
            memories_by_agent={"agent1": 60, "agent2": 40},
            avg_importance=0.75,
            oldest_memory=oldest,
            newest_memory=newest,
            storage_size_mb=15.5
        )
        
        assert stats.total_memories == 100
        assert stats.memories_by_type == {"text": 80, "json": 20}
        assert stats.memories_by_agent == {"agent1": 60, "agent2": 40}
        assert stats.avg_importance == 0.75
        assert stats.oldest_memory == oldest
        assert stats.newest_memory == newest
        assert stats.storage_size_mb == 15.5
    
    def test_memory_stats_optional_fields(self):
        """Test MemoryStats with optional fields."""
        stats = MemoryStats(
            total_memories=50,
            memories_by_type={"text": 50},
            memories_by_agent={"agent1": 50},
            avg_importance=0.8,
            oldest_memory=None,
            newest_memory=None
        )
        
        assert stats.total_memories == 50
        assert stats.oldest_memory is None
        assert stats.newest_memory is None
        assert stats.storage_size_mb is None  # Default value
    
    def test_memory_stats_to_dict(self):
        """Test MemoryStats to_dict conversion."""
        oldest = datetime.now() - timedelta(days=30)
        newest = datetime.now()
        
        stats = MemoryStats(
            total_memories=100,
            memories_by_type={"text": 80, "json": 20},
            memories_by_agent={"agent1": 60, "agent2": 40},
            avg_importance=0.75,
            oldest_memory=oldest,
            newest_memory=newest,
            storage_size_mb=15.5
        )
        
        dict_result = stats.to_dict()
        
        assert dict_result["total_memories"] == 100
        assert dict_result["memories_by_type"] == {"text": 80, "json": 20}
        assert dict_result["memories_by_agent"] == {"agent1": 60, "agent2": 40}
        assert dict_result["avg_importance"] == 0.75
        assert dict_result["oldest_memory"] == oldest.isoformat()
        assert dict_result["newest_memory"] == newest.isoformat()
        assert dict_result["storage_size_mb"] == 15.5
    
    def test_memory_stats_to_dict_with_none_dates(self):
        """Test MemoryStats to_dict with None datetime values."""
        stats = MemoryStats(
            total_memories=0,
            memories_by_type={},
            memories_by_agent={},
            avg_importance=0.0,
            oldest_memory=None,
            newest_memory=None
        )
        
        dict_result = stats.to_dict()
        
        assert dict_result["oldest_memory"] is None
        assert dict_result["newest_memory"] is None
        assert dict_result["storage_size_mb"] is None 