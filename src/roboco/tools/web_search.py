"""
Web Search Tool for Roboco

This module provides a tool for searching the web using the Tavily Search API.
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from loguru import logger

from tavily import TavilyClient
from roboco.core.tool import Tool
from roboco.core.logger import get_logger
from roboco.core.schema import ToolConfig

from langchain_core.tools import Tool as LangchainTool


class WebSearchConfig(ToolConfig):
    """Configuration for WebSearchTool."""
    api_key: Optional[str] = Field(
        default=None,
        description="Tavily API key"
    )
    max_results: int = Field(
        default=5,
        description="Maximum number of search results to return"
    )
    search_depth: str = Field(
        default="basic",
        description="Search depth, one of: 'basic' or 'comprehensive'"
    )
    include_domains: List[str] = Field(
        default_factory=list,
        description="List of domains to include in search results"
    )
    exclude_domains: List[str] = Field(
        default_factory=list,
        description="List of domains to exclude from search results"
    )
    include_answer: bool = Field(
        default=True,
        description="Whether to include an AI-generated answer"
    )
    include_raw_content: bool = Field(
        default=False,
        description="Whether to include raw page content"
    )
    include_images: bool = Field(
        default=False,
        description="Whether to include images in search results"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed requests"
    )
    timeout: int = Field(
        default=30,
        description="Request timeout in seconds"
    )


class WebSearchTool(Tool):
    """
    A tool for searching the web using the Tavily Search API.
    
    This tool provides a simple interface for searching the web and retrieving
    relevant information based on a query.
    """
    
    def __init__(
        self,
        config: Optional[WebSearchConfig] = None,
        **kwargs
    ):
        """
        Initialize the WebSearchTool.
        
        Args:
            config: Configuration for the web search tool
            **kwargs: Additional keyword arguments
        """
        super().__init__(config=config, **kwargs)
        
        # Initialize with config
        if config is None:
            config = WebSearchConfig()
        elif isinstance(config, dict):
            config = WebSearchConfig(**config)
            
        self.logger = get_logger(__name__)
        
        # Get API key from config or environment variable
        self.api_key = config.api_key or os.environ.get("TAVILY_API_KEY", "")
        if not self.api_key:
            self.logger.warning("Tavily API key not provided. Web search will not work.")
            
        # Initialize the Tavily client
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        
        # Store search configuration
        self.search_config = {
            "max_results": config.max_results,
            "search_depth": config.search_depth,
            "include_domains": config.include_domains,
            "exclude_domains": config.exclude_domains,
            "include_answer": config.include_answer,
            "include_raw_content": config.include_raw_content,
            "include_images": config.include_images
        }
        
        # Store retry and timeout configuration
        self.max_retries = config.max_retries
        self.timeout = config.timeout
        
        self.logger.info("Initialized WebSearchTool")
        
        # Define the search function
        async def search(query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
            """
            Search the web for information on a topic.
            
            Args:
                query: The search query
                max_results: Maximum number of results to return, overrides config setting
                
            Returns:
                Search results as a dictionary with query, results, and if enabled, an answer
            """
            if not self.client:
                self.logger.error("Tavily client not initialized. Cannot perform search.")
                return {
                    "error": "Search client not available. Please check your API key.",
                    "query": query,
                    "results": []
                }
                
            # Configure the search parameters
            search_params = self.search_config.copy()
            if max_results is not None:
                search_params["max_results"] = max_results
                
            self.logger.info(f"Searching for: {query}")
            
            # Perform the search with retries
            for attempt in range(self.max_retries):
                try:
                    # Perform the search
                    response = self.client.search(
                        query=query,
                        **search_params
                    )
                    
                    self.logger.info(f"Found {len(response.get('results', []))} results for query: {query}")
                    return response
                    
                except Exception as e:
                    self.logger.warning(f"Search attempt {attempt + 1}/{self.max_retries} failed: {e}")
                    if attempt == self.max_retries - 1:
                        # Return error on last attempt
                        self.logger.error(f"All retry attempts failed for query: {query}")
                        return {
                            "error": str(e),
                            "query": query,
                            "results": []
                        }
        
        # Register the search function
        self.register_function(
            name="web_search",
            description="Search the web for information on a topic",
            parameters={
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": None
                }
            },
            func_or_tool=search
        )

    @classmethod
    def create_with_config(cls, config: Optional[Dict[str, Any]] = None) -> "WebSearchTool":
        """Create a new instance of the WebSearchTool with the given configuration.
        
        Args:
            config: Configuration for the tool.
            
        Returns:
            A new WebSearchTool instance.
        """
        if config is None:
            config = {}
        return cls(config=WebSearchConfig(**config)) 