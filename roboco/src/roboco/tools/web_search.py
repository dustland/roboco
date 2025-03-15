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
            self.client = TavilyClient(api_key=self.api_key)
    
    def search(self, query: str, num_results: int = 5, include_domains: Optional[List[str]] = None, 
               exclude_domains: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search the web for information.
        
        Args:
            query: Search query
            num_results: Maximum number of results to return
            include_domains: Optional list of domains to include in search
            exclude_domains: Optional list of domains to exclude from search
            
        Returns:
            List of search results with title, snippet, and URL
        """
        if not self.api_key:
            return [{"error": "No API key provided for web search"}]
        
        if not TAVILY_AVAILABLE:
            return [{"error": "Tavily SDK not installed. Install with: pip install tavily-python"}]
        
        try:
            # Use Tavily SDK for web search
            if include_domains is None:
                include_domains = []
            if exclude_domains is None:
                exclude_domains = []
                
            search_params = {
                "query": query,
                "max_results": num_results,
                "search_depth": self.search_depth,
                "include_domains": include_domains,
                "exclude_domains": exclude_domains
            }
            
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
        
    def answer_question(self, question: str, search_depth: Optional[str] = None) -> Dict[str, Any]:
        """
        Ask Tavily to answer a question with web search-backed evidence.
        
        Args:
            question: The question to answer
            search_depth: Override the default search depth
            
        Returns:
            Dictionary containing the answer and sources
        """
        if not self.api_key:
            return {"error": "No API key provided for web search"}
        
        if not TAVILY_AVAILABLE:
            return {"error": "Tavily SDK not installed. Install with: pip install tavily-python"}
            
        try:
            # Use the Tavily question-answering endpoint
            depth = search_depth or self.search_depth
            
            response = self.client.qna(
                query=question,
                search_depth=depth,
                include_answer=True,
                include_raw_content=False
            )
            
            # Return a structured result with the answer and sources
            return {
                "answer": response.get("answer", "No answer found"),
                "sources": [
                    {"title": source.get("title", ""), "url": source.get("url", "")} 
                    for source in response.get("sources", [])
                ]
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {"error": str(e)}
    
    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """
        Get the function definitions for this tool.
        
        Returns:
            List of function definitions compatible with AG2
        """
        return [
            {
                "name": "web_search",
                "description": "Search the web for information on a specific topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find information about"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5)"
                        },
                        "include_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of domains to include in search"
                        },
                        "exclude_domains": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of domains to exclude from search"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "web_search_summarize",
                "description": "Search the web and get a formatted summary of results",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find information about"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to include in the summary (default: 5)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "answer_question",
                "description": "Ask a question and get an answer with sources from the web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "The question to answer using web search"
                        },
                        "search_depth": {
                            "type": "string",
                            "description": "Search depth: 'basic' (faster) or 'advanced' (more thorough)",
                            "enum": ["basic", "advanced"]
                        }
                    },
                    "required": ["question"]
                }
            }
        ]
        
    def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Execute a specific function with the given arguments.
        
        Args:
            function_name: Name of the function to execute
            arguments: Arguments to pass to the function
            
        Returns:
            Result of the function execution
        """
        if function_name == "web_search":
            return self.search(**arguments)
        elif function_name == "web_search_summarize":
            return self.search_and_summarize(**arguments)
        elif function_name == "answer_question":
            return self.answer_question(**arguments)
        else:
            return {"error": f"Unknown function: {function_name}"}