"""
Web Search Tool for Roboco

This module provides a tool for searching the web using the Tavily Search API.
"""

import os
from typing import Dict, Any, Optional, List
from loguru import logger

from tavily import TavilyClient
from roboco.core.tool import Tool


class WebSearchTool(Tool):
    """
    A tool for searching the web using the Tavily Search API.
    
    This tool provides a simple interface for searching the web and retrieving
    relevant information based on a query.
    """
    
    # Default search configuration
    default_search_config = {
        "max_results": 5,
        "search_depth": "basic",
        "include_domains": [],
        "exclude_domains": [],
        "include_answer": True,
        "include_raw_content": False,
        "include_images": False,
    }
    
    def __init__(
        self,
        api_key: str = None,
        search_config: Dict[str, Any] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        Initialize the WebSearchTool.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY environment variable)
            search_config: Configuration for search requests
            max_retries: Maximum number of retries for API calls
            timeout: Timeout for API calls in seconds
        """
        # Initialize the Tavily client
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        
        try:
            self.client = TavilyClient(api_key=self.api_key)
            logger.info("Tavily client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Tavily client: {e}")
            # Create a dummy client for testing
            self.client = None
        
        # Set configuration
        self.search_config = {**self.default_search_config, **(search_config or {})}
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Define the search function
        def search(query: str, max_results: Optional[int] = None) -> Dict[str, Any]:
            """
            Search the web for information based on a query.
            
            Args:
                query: The search query
                max_results: Maximum number of results to return (overrides search_config)
                
            Returns:
                A dictionary containing search results
            """
            if not query:
                return {
                    "success": False,
                    "error": "Query cannot be empty",
                    "results": [],
                    "answer": None,
                    "num_results": 0
                }
            
            # If the client is not initialized, return mock results
            if not self.client:
                logger.warning("Tavily client not initialized, returning mock results")
                return {
                    "success": True,
                    "query": query,
                    "results": [
                        {
                            "title": "Mock Result 1",
                            "url": "https://example.com/1",
                            "content": f"This is a mock result for the query: {query}",
                            "score": 0.95,
                            "raw_content": None
                        },
                        {
                            "title": "Mock Result 2",
                            "url": "https://example.com/2",
                            "content": f"Another mock result for: {query}",
                            "score": 0.85,
                            "raw_content": None
                        }
                    ],
                    "answer": f"This is a mock answer for the query: {query}",
                    "num_results": 2
                }
            
            # Create a copy of the search config
            config = dict(self.search_config)
            
            # Override max_results if provided
            if max_results is not None:
                config["max_results"] = max_results
            
            # Perform the search with retries
            for attempt in range(self.max_retries):
                try:
                    response = self.client.search(
                        query=query,
                        search_depth=config.get("search_depth", "basic"),
                        max_results=config.get("max_results", 5),
                        include_domains=config.get("include_domains", []),
                        exclude_domains=config.get("exclude_domains", []),
                        include_answer=config.get("include_answer", True),
                        include_raw_content=config.get("include_raw_content", False),
                        include_images=config.get("include_images", False),
                    )
                    
                    # Format the response
                    result = {
                        "success": True,
                        "query": query,
                        "results": response.get("results", []),
                        "answer": response.get("answer", ""),
                        "num_results": len(response.get("results", []))
                    }
                    
                    logger.info(f"Successfully searched for '{query}'")
                    return result
                    
                except Exception as e:
                    logger.warning(f"Search attempt {attempt + 1}/{self.max_retries} failed: {e}")
                    if attempt == self.max_retries - 1:
                        # Return error on last attempt
                        return {
                            "success": False,
                            "error": str(e),
                            "query": query,
                            "results": [],
                            "answer": None,
                            "num_results": 0
                        }
        
        # Initialize the Tool parent class with the search function
        super().__init__(
            name="search",
            description="Search the web for information using the Tavily Search API",
            func_or_tool=search
        )
        
        logger.info("Initialized WebSearchTool") 