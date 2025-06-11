"""
SERP API Search Tools for RoboCo

Provides web search capabilities using SERP API services.
Supports multiple search engines and search types.
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
from enum import Enum

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig

class SearchEngine(str, Enum):
    """Supported search engines"""
    GOOGLE = "google"
    BING = "bing"
    YAHOO = "yahoo"
    BAIDU = "baidu"
    YANDEX = "yandex"
    DUCKDUCKGO = "duckduckgo"

class SearchType(str, Enum):
    """Supported search types"""
    WEB = "web"
    NEWS = "news"
    IMAGES = "images"
    ACADEMIC = "academic"

class SerpSearchTool(AbstractTool):
    """
    Web search tool using SERP API.
    
    Provides comprehensive web search capabilities with support for multiple
    search engines, search types, and localization options.
    """
    
    def __init__(self, serpapi_key: Optional[str] = None):
        """
        Initialize SERP search tool.
        
        Args:
            serpapi_key: SERP API key. If not provided, will use SERPAPI_KEY env var.
        """
        self.serpapi_key = serpapi_key or os.getenv("SERPAPI_KEY")
        
        if not self.serpapi_key:
            raise ValueError(
                "SERPAPI_KEY is required. Set it as environment variable or pass to constructor."
            )
        
        # Try to import serpapi package
        try:
            import serpapi
            self.serpapi = serpapi
            self._serpapi_available = True
        except ImportError:
            raise ImportError(
                "serpapi package is required. Install it with: pip install google-search-results"
            )
        
        # Initialize search classes
        self._search_classes = {}
        try:
            from serpapi import (
                GoogleSearch, BingSearch, BaiduSearch, YahooSearch, 
                DuckDuckGoSearch, YandexSearch
            )
            self._search_classes = {
                SearchEngine.GOOGLE: GoogleSearch,
                SearchEngine.BING: BingSearch,
                SearchEngine.BAIDU: BaiduSearch,
                SearchEngine.YAHOO: YahooSearch,
                SearchEngine.DUCKDUCKGO: DuckDuckGoSearch,
                SearchEngine.YANDEX: YandexSearch
            }
        except ImportError as e:
            raise ImportError(f"Failed to import SERP API search classes: {e}")

    @property
    def name(self) -> str:
        return "serp_search"

    @property
    def description(self) -> str:
        return "Search the web using SERP API with support for multiple search engines and types"

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="query",
                type="string",
                description="The search query to execute",
                required=True
            ),
            ToolParameterConfig(
                name="engine",
                type="string",
                description="Search engine to use (google, bing, yahoo, baidu, yandex, duckduckgo)",
                required=False,
                default="google"
            ),
            ToolParameterConfig(
                name="search_type",
                type="string", 
                description="Type of search (web, news, images, academic)",
                required=False,
                default="web"
            ),
            ToolParameterConfig(
                name="max_results",
                type="integer",
                description="Maximum number of results to return (1-20)",
                required=False,
                default=10
            ),
            ToolParameterConfig(
                name="country",
                type="string",
                description="Country code for localized results (e.g., 'us', 'cn', 'jp')",
                required=False,
                default="us"
            ),
            ToolParameterConfig(
                name="language",
                type="string",
                description="Language code for results (e.g., 'en', 'zh', 'ja')",
                required=False,
                default="en"
            )
        ]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "serpapi_key": {
                    "type": "string",
                    "description": "SERP API key for authentication"
                }
            }
        }

    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute web search using SERP API.
        
        Args:
            input_data: Dictionary containing search parameters
            config: Optional configuration overrides
            
        Returns:
            Dictionary containing search results and metadata
        """
        # Extract parameters
        query = input_data.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        
        engine = input_data.get("engine", "google").lower()
        search_type = input_data.get("search_type", "web").lower()
        max_results = min(input_data.get("max_results", 10), 20)  # Cap at 20
        country = input_data.get("country", "us")
        language = input_data.get("language", "en")
        
        # Validate engine
        try:
            search_engine = SearchEngine(engine)
        except ValueError:
            raise ValueError(f"Unsupported search engine: {engine}")
        
        # Validate search type
        try:
            search_type_enum = SearchType(search_type)
        except ValueError:
            raise ValueError(f"Unsupported search type: {search_type}")
        
        start_time = datetime.now()
        
        try:
            # Get search class
            search_class = self._search_classes.get(search_engine)
            if not search_class:
                raise ValueError(f"Search class not available for engine: {engine}")
            
            # Prepare search parameters
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "num": max_results,
                "gl": country,
                "hl": language,
            }
            
            # Add search type specific parameters
            if search_type_enum == SearchType.NEWS:
                params["tbm"] = "nws"
            elif search_type_enum == SearchType.IMAGES:
                params["tbm"] = "isch"
            elif search_type_enum == SearchType.ACADEMIC and search_engine == SearchEngine.GOOGLE:
                # Use GoogleScholarSearch for academic
                try:
                    from serpapi import GoogleScholarSearch
                    search_class = GoogleScholarSearch
                except ImportError:
                    pass
            
            # Execute search (synchronous operation)
            loop = asyncio.get_event_loop()
            search_result = await loop.run_in_executor(
                None, 
                lambda: search_class(params).get_dict()
            )
            
            # Parse results
            results = self._parse_search_results(search_result, query)
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query": query,
                "engine": engine,
                "search_type": search_type,
                "results": results,
                "total_results": len(results),
                "response_time": response_time,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            error_msg = f"Search failed for '{query}' using {engine}: {str(e)}"
            return {
                "query": query,
                "engine": engine,
                "search_type": search_type,
                "results": [],
                "total_results": 0,
                "error": error_msg,
                "success": False,
                "timestamp": datetime.now().isoformat()
            }

    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """
        Stream search results as they become available.
        
        For search operations, this returns the full result set since 
        SERP API returns results all at once.
        """
        result = await self.run(input_data, config)
        yield result

    def _parse_search_results(self, search_data: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """
        Parse SERP API response into standardized result format.
        
        Args:
            search_data: Raw response from SERP API
            query: Original search query
            
        Returns:
            List of parsed search results
        """
        results = []
        
        # Extract organic results
        organic_results = search_data.get("organic_results", [])
        
        for i, result in enumerate(organic_results):
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            url = result.get("link", "")
            
            # Generate enhanced summary
            summary = self._generate_summary(title, snippet, query)
            
            # Detect language (simple approach)
            language = self._detect_language(snippet + " " + title)
            
            parsed_result = {
                "title": title,
                "url": url,
                "snippet": snippet,
                "summary": summary,
                "position": result.get("position", i + 1),
                "displayed_link": result.get("displayed_link", ""),
                "language": language,
                "score": max(0.1, 1.0 - (i * 0.1)),  # Position-based scoring
                "metadata": {
                    "cached_page_link": result.get("cached_page_link"),
                    "related_links": result.get("related_links", []),
                    "rich_snippet": result.get("rich_snippet"),
                    "date": result.get("date"),
                    "source": "serpapi"
                }
            }
            
            results.append(parsed_result)
        
        return results

    def _generate_summary(self, title: str, snippet: str, query: str) -> str:
        """
        Generate an enhanced summary from title and snippet.
        
        Args:
            title: Result title
            snippet: Result snippet
            query: Original search query
            
        Returns:
            Enhanced summary text
        """
        if not snippet and not title:
            return "No summary available"
        
        clean_snippet = snippet.strip() if snippet else ""
        clean_title = title.strip() if title else ""
        
        # Combine title and snippet intelligently
        if clean_title and clean_snippet:
            if clean_title.lower() in clean_snippet.lower():
                summary = clean_snippet
            else:
                summary = f"{clean_title}. {clean_snippet}"
        elif clean_title:
            summary = clean_title
        elif clean_snippet:
            summary = clean_snippet
        else:
            summary = "No summary available"
        
        # Ensure minimum length
        if len(summary) < 50 and clean_snippet:
            summary = clean_snippet
        
        # Add query context if too short
        if len(summary) < 30 and query:
            summary = f"Result for '{query}': {summary}"
        
        # Limit length for efficiency
        if len(summary) > 500:
            summary = summary[:497] + "..."
        
        return summary

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on character analysis.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code (en, zh, ja, etc.)
        """
        if not text:
            return "unknown"
        
        # Chinese character detection
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        if chinese_chars > len(text) * 0.1:
            return "zh"
        
        # Japanese character detection (hiragana, katakana)
        japanese_chars = sum(1 for char in text if 
                           ('\u3040' <= char <= '\u309f') or  # Hiragana
                           ('\u30a0' <= char <= '\u30ff'))    # Katakana
        if japanese_chars > len(text) * 0.1:
            return "ja"
        
        # Korean character detection
        korean_chars = sum(1 for char in text if '\uac00' <= char <= '\ud7af')
        if korean_chars > len(text) * 0.1:
            return "ko"
        
        # Default to English
        return "en"


class MultiEngineSearchTool(AbstractTool):
    """
    Multi-engine search tool that queries multiple search engines in parallel.
    """
    
    def __init__(self, serpapi_key: Optional[str] = None):
        """Initialize multi-engine search tool."""
        self.serp_tool = SerpSearchTool(serpapi_key)

    @property
    def name(self) -> str:
        return "multi_engine_search"

    @property
    def description(self) -> str:
        return "Search across multiple search engines simultaneously for comprehensive results"

    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        return [
            ToolParameterConfig(
                name="query",
                type="string",
                description="The search query to execute across all engines",
                required=True
            ),
            ToolParameterConfig(
                name="engines",
                type="array",
                description="List of search engines to use (default: ['google', 'bing'])",
                required=False,
                default=["google", "bing"]
            ),
            ToolParameterConfig(
                name="max_results",
                type="integer",
                description="Maximum number of results per engine (1-10)",
                required=False,
                default=5
            ),
            ToolParameterConfig(
                name="country",
                type="string",
                description="Country code for localized results",
                required=False,
                default="us"
            ),
            ToolParameterConfig(
                name="language",
                type="string",
                description="Language code for results",
                required=False,
                default="en"
            )
        ]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "serpapi_key": {
                    "type": "string",
                    "description": "SERP API key for authentication"
                }
            }
        }

    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute parallel searches across multiple engines.
        
        Args:
            input_data: Dictionary containing search parameters
            config: Optional configuration overrides
            
        Returns:
            Dictionary containing aggregated results from all engines
        """
        query = input_data.get("query")
        if not query:
            raise ValueError("Query parameter is required")
        
        engines = input_data.get("engines", ["google", "bing"])
        max_results = min(input_data.get("max_results", 5), 10)
        country = input_data.get("country", "us")
        language = input_data.get("language", "en")
        
        start_time = datetime.now()
        
        # Create search tasks for each engine
        tasks = []
        for engine in engines:
            search_params = {
                "query": query,
                "engine": engine,
                "max_results": max_results,
                "country": country,
                "language": language
            }
            task = self.serp_tool.run(search_params)
            tasks.append((engine, task))
        
        # Execute searches in parallel
        engine_results = {}
        all_results = []
        total_results = 0
        
        for engine, task in tasks:
            try:
                result = await task
                engine_results[engine] = result
                
                if result.get("success", False):
                    # Add engine info to each result
                    for res in result.get("results", []):
                        res["search_engine"] = engine
                        all_results.append(res)
                    total_results += result.get("total_results", 0)
                    
            except Exception as e:
                engine_results[engine] = {
                    "success": False,
                    "error": str(e),
                    "results": []
                }
        
        # Sort all results by score (best first)
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "query": query,
            "engines": engines,
            "aggregated_results": all_results,
            "engine_results": engine_results,
            "total_results": total_results,
            "successful_engines": [e for e, r in engine_results.items() if r.get("success", False)],
            "response_time": response_time,
            "timestamp": datetime.now().isoformat(),
            "success": len(all_results) > 0
        }

    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """Stream multi-engine search results."""
        result = await self.run(input_data, config)
        yield result 