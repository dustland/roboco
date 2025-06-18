"""
Memory System Package

Provides intelligent memory management with event-driven synthesis and context injection.
"""

from .backend import MemoryBackend
from .factory import create_memory_backend, create_default_memory_backend
from .types import (
    MemoryItem, 
    MemoryQuery, 
    MemorySearchResult, 
    MemoryStats, 
    MemoryType,
    # Specialized memory types for synthesis engine
    Memory,
    Constraint,
    HotIssue,
    DocumentChunk
)

# New memory system components
from .synthesis_engine import MemorySynthesisEngine
from .memory_system import MemorySystem, create_memory_system

__all__ = [
    # Core memory components
    "MemoryBackend",
    "create_memory_backend",
    "create_default_memory_backend",
    
    # Data types
    "MemoryItem",
    "MemoryQuery",
    "MemorySearchResult",
    "MemoryStats",
    "MemoryType",
    
    # Specialized memory types
    "Memory",
    "Constraint",
    "HotIssue", 
    "DocumentChunk",
    
    # Synthesis engine and system
    "MemorySynthesisEngine",
    "MemorySystem",
    "create_memory_system",
] 