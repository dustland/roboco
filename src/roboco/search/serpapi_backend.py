"""
SerpAPI backend implementation for web search.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from serpapi import GoogleSearch, BingSearch, BaiduSearch, YahooSearch, DuckDuckGoSearch, YandexSearch

from .interfaces import SearchBackend, SearchResult, SearchResponse, SearchEngine


class SerpAPIBackend(SearchBackend):
    """Search backend using SerpAPI service."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SerpAPI backend.
        
        Args:
            api_key: SerpAPI key. If not provided, uses SERPAPI_KEY environment variable.
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        
        if not self.api_key:
            raise ValueError(
                "SERPAPI_KEY is required. Set it as environment variable or pass api_key to constructor."
            )
        
        self._search_classes = {
            SearchEngine.GOOGLE: GoogleSearch,
            SearchEngine.BING: BingSearch,
            SearchEngine.BAIDU: BaiduSearch,
            SearchEngine.YAHOO: YahooSearch,
            SearchEngine.DUCKDUCKGO: DuckDuckGoSearch,
            SearchEngine.YANDEX: YandexSearch
        }

    @property
    def name(self) -> str:
        return "serpapi"

    def is_available(self) -> bool:
        """Check if SerpAPI backend is available."""
        return bool(self.api_key)

    async def search(self, query: str, engine: str = "google", 
                    max_results: int = 10, country: str = "us", 
                    language: str = "en", **kwargs) -> SearchResponse:
        """
        Execute search using SerpAPI.
        
        Args:
            query: Search query
            engine: Search engine to use
            max_results: Maximum number of results (capped at 20)
            country: Country code for localization
            language: Language code for results
            **kwargs: Additional search parameters
            
        Returns:
            SearchResponse with results and metadata
        """
        # Validate engine
        try:
            search_engine = SearchEngine(engine.lower())
        except ValueError:
            raise ValueError(f"Unsupported search engine: {engine}")
        
        start_time = datetime.now()
        
        try:
            # Get search class
            search_class = self._search_classes.get(search_engine)
            if not search_class:
                raise ValueError(f"Search class not available for engine: {engine}")
            
            # Prepare search parameters
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": min(max_results, 20),  # Cap at 20
                "gl": country,
                "hl": language,
            }
            
            # Add any additional parameters
            params.update(kwargs)
            
            # Execute search
            search = search_class(params)
            search_data = search.get_dict()
            
            # Parse results
            results = self._parse_search_results(search_data, query)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return SearchResponse(
                query=query,
                engine=engine,
                results=results,
                total_results=len(results),
                response_time=response_time,
                timestamp=datetime.now().isoformat(),
                success=True
            )
            
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            return SearchResponse(
                query=query,
                engine=engine,
                results=[],
                total_results=0,
                response_time=response_time,
                timestamp=datetime.now().isoformat(),
                success=False,
                error=str(e)
            )

    def _parse_search_results(self, search_data: Dict[str, Any], query: str) -> List[SearchResult]:
        """Parse SerpAPI response into SearchResult objects."""
        results = []
        
        # Get organic results
        organic_results = search_data.get("organic_results", [])
        
        for i, result in enumerate(organic_results):
            title = result.get("title", "")
            link = result.get("link", "")
            snippet = result.get("snippet", "")
            
            if title and link:
                search_result = SearchResult(
                    title=title,
                    url=link,
                    snippet=snippet,
                    position=i + 1,
                    relevance_score=self._calculate_relevance_score(title, snippet, query),
                    language=self._detect_language(f"{title} {snippet}"),
                    date=result.get("date"),
                    displayed_link=result.get("displayed_link"),
                    summary=self._generate_summary(title, snippet, query)
                )
                
                results.append(search_result)
        
        return results

    def _generate_summary(self, title: str, snippet: str, query: str) -> str:
        """Generate a concise summary of the search result."""
        # Combine title and snippet
        full_text = f"{title}. {snippet}".strip()
        
        # Remove duplicate periods
        full_text = full_text.replace("..", ".")
        
        # Limit to reasonable length
        if len(full_text) > 200:
            # Try to cut at sentence boundary
            sentences = full_text.split(". ")
            summary = sentences[0]
            
            for sentence in sentences[1:]:
                if len(summary + ". " + sentence) <= 200:
                    summary += ". " + sentence
                else:
                    break
            
            full_text = summary
        
        return full_text

    def _calculate_relevance_score(self, title: str, snippet: str, query: str) -> float:
        """Calculate relevance score based on keyword matching."""
        text = f"{title} {snippet}".lower()
        query_terms = query.lower().split()
        
        if not query_terms:
            return 0.0
        
        score = 0.0
        for term in query_terms:
            # Title matches are weighted more heavily
            title_matches = title.lower().count(term) * 2
            snippet_matches = snippet.lower().count(term)
            score += title_matches + snippet_matches
        
        # Normalize by query length
        return min(score / len(query_terms), 10.0)

    def _detect_language(self, text: str) -> str:
        """Detect language of text content."""
        if not text:
            return "unknown"
        
        # Simple heuristic - could be improved with proper language detection
        return "en"  # Default to English for now 