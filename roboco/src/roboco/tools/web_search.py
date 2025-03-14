"""
Web Search Tool

This module provides a tool for searching the web and retrieving information,
designed to be compatible with AG2's function calling mechanism.
"""

import os
import json
import requests
from typing import List, Dict, Any, Optional
from loguru import logger

from roboco.tools.base import Tool

class WebSearchTool(Tool):
    """Tool for performing web searches and retrieving information."""
    
    def __init__(self, api_key: Optional[str] = None, search_engine: str = "google"):
        """
        Initialize the web search tool.
        
        Args:
            api_key: API key for the search provider (optional, falls back to env var)
            search_engine: Name of the search engine to use (default: google)
        """
        super().__init__(name="web_search", description="Search the web for information")
        
        # Set up API key (from parameter or environment variable)
        self.api_key = api_key or os.environ.get("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("No SERPAPI_API_KEY provided, web search will not work")
            
        self.search_engine = search_engine
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not self.api_key:
            return [{"error": "No API key provided for web search"}]
        
        try:
            # Use SerpAPI for web search
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": self.search_engine,
                "num": num_results
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Process search results
            results = []
            if "organic_results" in data:
                for result in data["organic_results"][:num_results]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("snippet", ""),
                        "url": result.get("link", "")
                    })
            
            return results
        
        except Exception as e:
            logger.error(f"Error performing web search: {e}")
            return [{"error": str(e)}]
    
    def search_and_summarize(self, query: str, num_results: int = 5) -> str:
        """
        Search the web and provide a summarized response.
        
        Args:
            query: Search query
            num_results: Number of results to include
            
        Returns:
            A formatted string with search results
        """
        results = self.search(query, num_results)
        
        if results and "error" in results[0]:
            return f"Error performing search: {results[0]['error']}"
        
        # Format the results as a markdown string
        summary = f"## Search Results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            summary += f"### {i}. {result['title']}\n"
            summary += f"{result['snippet']}\n"
            summary += f"[Read more]({result['url']})\n\n"
        
        return summary