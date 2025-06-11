"""
Search interfaces and base classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SearchEngine(str, Enum):
    """Supported search engines"""
    GOOGLE = "google"
    BING = "bing"
    YAHOO = "yahoo"
    BAIDU = "baidu"
    YANDEX = "yandex"
    DUCKDUCKGO = "duckduckgo"


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    position: int
    relevance_score: float
    language: str = "en"
    date: Optional[str] = None
    displayed_link: Optional[str] = None
    summary: Optional[str] = None


@dataclass
class SearchResponse:
    """Represents a complete search response."""
    query: str
    engine: str
    results: List[SearchResult]
    total_results: int
    response_time: float
    timestamp: str
    success: bool
    error: Optional[str] = None


class SearchBackend(ABC):
    """Abstract base class for search backends."""
    
    @abstractmethod
    async def search(self, query: str, engine: str = "google", 
                    max_results: int = 10, country: str = "us", 
                    language: str = "en", **kwargs) -> SearchResponse:
        """Execute a search query."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the backend is available and properly configured."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name."""
        pass 