"""
Web Search Tool

This module provides a tool for searching the web and retrieving information,
designed to be compatible with AG2's function calling mechanism.
"""

import os
import json
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    logger.warning("Tavily SDK not installed. Install with: pip install tavily-python")
    TAVILY_AVAILABLE = False

from roboco.core.tool import Tool


class WebSearchTool(Tool):
    """Tool for performing web searches and retrieving information."""
    
    def __init__(self, api_key: Optional[str] = None, search_depth: str = "basic"):
        """
        Initialize the web search tool.
        
        Args:
            api_key: Tavily API key (optional, falls back to env var)
            search_depth: Search depth - 'basic' or 'advanced' (affects quota usage)
        """
        super().__init__(name="web_search", description="Search the web for information")
        
        # Set up API key (from parameter or environment variable)
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        if not self.api_key:
            logger.warning("No TAVILY_API_KEY provided, web search will not work")
        
        self.search_depth = search_depth
        self.client = None
        
        # Initialize Tavily client if available
        if TAVILY_AVAILABLE and self.api_key:
            try:
                self.client = TavilyClient(api_key=self.api_key)
                logger.info("Successfully initialized Tavily client")
            except Exception as e:
                logger.error(f"Failed to initialize Tavily client: {e}")
        elif not TAVILY_AVAILABLE:
            logger.error("Tavily SDK not installed. Install with: pip install tavily-python")
        elif not self.api_key:
            logger.error("TAVILY_API_KEY not set. Please set it in your environment variables.")
    
    def search(self, query: str, num_results: int = 5, include_domains: Optional[List[str]] = None, 
               exclude_domains: Optional[List[str]] = None) -> List[Dict[str, str]]:
        """
        Search the web for information on a specific topic.
        
        Args:
            query: The search query to find information about
            num_results: Number of results to return (default: 5)
            include_domains: Optional list of domains to include in search
            exclude_domains: Optional list of domains to exclude from search
            
        Returns:
            List of search results, each containing title, snippet, and URL
        """
        if not TAVILY_AVAILABLE:
            return [{"error": "Tavily SDK not installed. Install with: pip install tavily-python"}]
        
        if not self.client:
            return [{"error": "Tavily client not initialized. Check your API key."}]
        
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "search_depth": self.search_depth,
                "max_results": num_results
            }
            
            # Add optional parameters if provided
            if include_domains:
                search_params["include_domains"] = include_domains
            if exclude_domains:
                search_params["exclude_domains"] = exclude_domains
                
            # Execute search
            logger.info(f"Performing web search for: {query}")
            response = self.client.search(**search_params)
            
            # Process search results
            results = []
            if "results" in response:
                for result in response["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "snippet": result.get("content", ""),
                        "url": result.get("url", "")
                    })
                logger.info(f"Web search returned {len(results)} results")
            else:
                logger.warning(f"Web search returned no results. Raw response: {response}")
            
            return results
        
        except Exception as e:
            error_msg = f"Error performing web search: {e}"
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return [{"error": error_msg}]
    
    def search_and_summarize(self, query: str, num_results: int = 5) -> str:
        """
        Search the web and provide a summarized response.
        
        Args:
            query: The search query to find information about
            num_results: Number of results to include in the summary (default: 5)
            
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
        
    def answer_question(self, question: str, search_depth: Optional[str] = None) -> Dict[str, str]:
        """
        Ask a question and get an answer with sources from the web.
        
        Args:
            question: The question to answer
            search_depth: Optional search depth override (basic or comprehensive)
            
        Returns:
            Dictionary with answer and sources
        """
        if not TAVILY_AVAILABLE:
            return {"error": "Tavily SDK not installed. Install with: pip install tavily-python"}
        
        if not self.client:
            return {"error": "Tavily client not initialized. Check your API key."}
        
        try:
            # Use the provided search_depth or fall back to the instance default
            depth = search_depth or self.search_depth
            
            # Use Tavily's question answering endpoint
            logger.info(f"Asking question: {question}")
            response = self.client.qna(query=question, search_depth=depth)
            
            # Format the response
            answer = response.get("answer", "No answer found")
            sources = []
            
            if "sources" in response:
                for source in response["sources"]:
                    sources.append({
                        "title": source.get("title", ""),
                        "url": source.get("url", "")
                    })
            
            return {
                "answer": answer,
                "sources": sources
            }
            
        except Exception as e:
            error_msg = f"Error answering question: {e}"
            logger.error(error_msg)
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": error_msg}
    
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a specific function with the given arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Dictionary of arguments to pass to the function
            
        Returns:
            Result of the function execution
        """
        # This method is only needed for backward compatibility
        # with tools that still use the old AG2 approach
        if function_name == "web_search":
            return self.search(**arguments)
        elif function_name == "web_search_summarize":
            return self.search_and_summarize(**arguments)
        elif function_name == "answer_question":
            return self.answer_question(**arguments)
        else:
            error_msg = f"Unknown function: {function_name}"
            logger.error(error_msg)
            return {"error": error_msg}