"""
AgentX Search Module

Provides web search capabilities with multiple backend implementations.
"""

from .interfaces import SearchBackend, SearchResult, SearchResponse
from .serpapi_backend import SerpAPIBackend
from .search_manager import SearchManager

__all__ = [
    "SearchBackend",
    "SearchResult",
    "SearchResponse",
    "SerpAPIBackend", 
    "SearchManager",
] 