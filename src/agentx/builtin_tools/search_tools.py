"""
Search Tools - Web search capabilities using SerpAPI.

Built-in integration with SerpAPI for comprehensive web search across
multiple search engines (Google, Bing, DuckDuckGo, etc.).
"""

from ..utils.logger import get_logger
from ..tool.models import Tool, tool, ToolResult
from ..search.serpapi_backend import SerpAPIBackend
from ..search.interfaces import SearchEngine
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Individual search result."""
    title: str
    url: str
    snippet: str
    position: int
    relevance_score: float
    language: str = "en"
    date: Optional[str] = None
    displayed_link: Optional[str] = None
    summary: Optional[str] = None


class SearchTool(Tool):
    """
    Web search tool using SerpAPI.
    
    Provides access to multiple search engines including Google, Bing,
    DuckDuckGo, Yahoo, Baidu, and Yandex through a unified interface.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("search")
        self.api_key = api_key
        self._backend = None
        self._init_backend()
    
    def _init_backend(self):
        """Initialize SerpAPI backend."""
        try:
            self._backend = SerpAPIBackend(self.api_key)
            logger.info("SerpAPI search backend initialized")
        except ValueError as e:
            logger.error(f"Failed to initialize SerpAPI backend: {e}")
        except Exception as e:
            logger.error(f"Unexpected error initializing search backend: {e}")
    
    @tool(
        description="Search the web using Google, Bing, DuckDuckGo or other search engines",
        return_description="ToolResult containing list of search results with titles, URLs, and snippets"
    )
    async def web_search(self, query: str, engine: str = "google", 
                        max_results: int = 10, country: str = "us", 
                        language: str = "en") -> ToolResult:
        """
        Search the web using various search engines.
        
        Args:
            query: Search query to execute (required)
            engine: Search engine to use - google, bing, duckduckgo, yahoo, baidu, yandex (default: google)
            max_results: Maximum number of results to return, max 20 (default: 10)
            country: Country code for localized results (default: us)
            language: Language code for results (default: en)
            
        Returns:
            ToolResult containing search results and metadata
        """
        if not self._backend:
            return ToolResult(
                success=False,
                result=None,
                error="Search backend not available. Check SERPAPI_KEY environment variable."
            )
        
        try:
            # Execute search
            response = await self._backend.search(
                query=query,
                engine=engine,
                max_results=min(max_results, 20),  # Cap at 20
                country=country,
                language=language
            )
            
            if response.success:
                # Convert to our SearchResult format
                search_results = [
                    SearchResult(
                        title=result.title,
                        url=result.url,
                        snippet=result.snippet,
                        position=result.position,
                        relevance_score=result.relevance_score,
                        language=result.language,
                        date=result.date,
                        displayed_link=result.displayed_link,
                        summary=result.summary
                    )
                    for result in response.results
                ]
                
                return ToolResult(
                    success=True,
                    result=search_results,
                    execution_time=response.response_time,
                    metadata={
                        "query": query,
                        "engine": engine,
                        "total_results": response.total_results,
                        "country": country,
                        "language": language,
                        "timestamp": response.timestamp
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=response.error or "Search failed",
                    execution_time=response.response_time
                )
                
        except Exception as e:
            logger.error(f"Web search failed for query '{query}': {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    @tool(
        description="Search for news articles using Google News or Bing News",
        return_description="ToolResult containing list of news search results with articles and publication dates"
    )
    async def news_search(self, query: str, engine: str = "google", 
                         max_results: int = 10, country: str = "us") -> ToolResult:
        """
        Search for news articles.
        
        Args:
            query: News search query (required)
            engine: Search engine to use - google or bing (default: google)
            max_results: Maximum number of news results (default: 10)
            country: Country code for localized news (default: us)
            
        Returns:
            ToolResult containing news search results
        """
        if not self._backend:
            return ToolResult(
                success=False,
                result=None,
                error="Search backend not available"
            )
        
        try:
            # Add news-specific parameters
            response = await self._backend.search(
                query=query,
                engine=engine,
                max_results=min(max_results, 20),
                country=country,
                tbm="nws"  # Google News search
            )
            
            if response.success:
                return ToolResult(
                    success=True,
                    result=response.results,
                    execution_time=response.response_time,
                    metadata={
                        "query": query,
                        "engine": engine,
                        "search_type": "news",
                        "total_results": response.total_results,
                        "timestamp": response.timestamp
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=response.error or "News search failed"
                )
                
        except Exception as e:
            logger.error(f"News search failed for query '{query}': {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )
    
    @tool(
        description="Search for images using Google Images or Bing Images",
        return_description="ToolResult containing list of image search results with URLs and metadata"
    )
    async def image_search(self, query: str, engine: str = "google", 
                          max_results: int = 10, safe_search: str = "moderate") -> ToolResult:
        """
        Search for images.
        
        Args:
            query: Image search query (required)
            engine: Search engine to use - google or bing (default: google)
            max_results: Maximum number of image results (default: 10)
            safe_search: Safe search setting - off, moderate, strict (default: moderate)
            
        Returns:
            ToolResult containing image search results
        """
        if not self._backend:
            return ToolResult(
                success=False,
                result=None,
                error="Search backend not available"
            )
        
        try:
            response = await self._backend.search(
                query=query,
                engine=engine,
                max_results=min(max_results, 20),
                tbm="isch",  # Google Images search
                safe=safe_search
            )
            
            if response.success:
                return ToolResult(
                    success=True,
                    result=response.results,
                    execution_time=response.response_time,
                    metadata={
                        "query": query,
                        "engine": engine,
                        "search_type": "images",
                        "safe_search": safe_search,
                        "total_results": response.total_results,
                        "timestamp": response.timestamp
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    result=None,
                    error=response.error or "Image search failed"
                )
                
        except Exception as e:
            logger.error(f"Image search failed for query '{query}': {e}")
            return ToolResult(
                success=False,
                result=None,
                error=str(e)
            )


# Export main classes and functions
__all__ = [
    "SearchTool",
    "SearchResult",
]

