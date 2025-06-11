"""
Web Search Tools for RoboCo

Thin wrapper around the roboco.search module that provides tool interfaces
for the agent system.
"""

from typing import Dict, List, Optional, Any, AsyncGenerator

from roboco.tool.interfaces import AbstractTool
from roboco.config.models import ToolParameterConfig
from roboco.search import SearchManager


class WebSearchTool(AbstractTool):
    """
    Web search tool that provides a clean interface to multiple search backends.
    
    This is the main search tool that should be used by agents. It automatically
    handles backend selection and provides a consistent interface regardless of
    the underlying search provider.
    """
    
    def __init__(self, api_key: Optional[str] = None, backend: str = "serpapi", **backend_configs):
        """
        Initialize web search tool.
        
        Args:
            api_key: Search API key (primarily for SerpAPI)
            backend: Default search backend to use
            **backend_configs: Additional configuration for search backends
        """
        # Set up backend configurations
        if api_key:
            backend_configs.setdefault("serpapi", {})["api_key"] = api_key
        
        # Initialize search manager
        self.search_manager = SearchManager(
            default_backend=backend,
            **backend_configs
        )

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web for information on any topic using multiple search engines"

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
            ),
            ToolParameterConfig(
                name="backend",
                type="string",
                description="Search backend to use (serpapi)",
                required=False,
                default="serpapi"
            )
        ]

    @classmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_key": {
                    "type": "string",
                    "description": "Search API key for authentication"
                },
                "backend": {
                    "type": "string",
                    "description": "Default search backend (serpapi)",
                    "default": "serpapi"
                }
            }
        }

    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute web search.
        
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
        
        search_params = {
            "engine": input_data.get("engine", "google"),
            "max_results": input_data.get("max_results", 10),
            "country": input_data.get("country", "us"),
            "language": input_data.get("language", "en"),
        }
        
        backend = input_data.get("backend")
        
        try:
            # Execute search
            response = await self.search_manager.search(
                query=query,
                backend=backend,
                **search_params
            )
            
            # Convert SearchResponse to dictionary format expected by tools
            return {
                "query": response.query,
                "engine": response.engine,
                "results": [
                    {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet,
                        "position": result.position,
                        "relevance_score": result.relevance_score,
                        "language": result.language,
                        "date": result.date,
                        "displayed_link": result.displayed_link,
                        "summary": result.summary,
                    }
                    for result in response.results
                ],
                "total_results": response.total_results,
                "response_time": response.response_time,
                "timestamp": response.timestamp,
                "success": response.success,
                "error": response.error,
                "backend_used": backend or self.search_manager.default_backend
            }
            
        except Exception as e:
            return {
                "query": query,
                "engine": search_params.get("engine", "google"),
                "results": [],
                "total_results": 0,
                "error": str(e),
                "success": False,
                "timestamp": None,
                "backend_used": backend or self.search_manager.default_backend
            }

    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """Stream search results."""
        result = await self.run(input_data, config)
        yield result


# Aliases for backward compatibility
SerpSearchTool = WebSearchTool
SerpWebSearchTool = WebSearchTool 