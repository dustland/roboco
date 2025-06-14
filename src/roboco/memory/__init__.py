"""
Memory Backend Module

Provides intelligent memory management with Mem0 integration for multi-agent
collaboration workflows.

This module handles the complex backend implementation while keeping the
core memory interface simple and clean.
"""

from .backend import MemoryBackend
from .mem0_backend import Mem0Backend
from .types import MemoryItem, MemoryQuery, MemorySearchResult, MemoryType, MemoryStats
from .factory import create_memory_backend, create_default_memory_backend

__all__ = [
    "MemoryBackend",
    "Mem0Backend", 
    "MemoryItem",
    "MemoryQuery",
    "MemorySearchResult",
    "MemoryType",
    "MemoryStats",
    "create_memory_backend",
    "create_default_memory_backend"
] 