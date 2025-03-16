"""
Browser Tool

This module provides a tool for web browsing and page interaction,
designed to be compatible with autogen's function calling mechanism.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from browser_use import Browser

from roboco.core.tool import Tool

class BrowserTool(Tool):
    """Tool for web browsing and information extraction."""
    
    def __init__(
        self,
        search: Optional[Dict[str, Any]] = None,
        browse: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Initialize the browser tool.
        
        Args:
            search: Search-specific settings
            browse: Browse-specific settings
            use_cache: Whether to use caching
            max_retries: Maximum number of retry attempts
            timeout: Operation timeout in seconds
        """
        super().__init__(
            name="browser",
            description="Tool for web browsing and information extraction"
        )
        
        # Store configuration
        self.search_config = search or {"max_results": 5, "timeout": timeout}
        self.browse_config = browse or {"timeout": timeout, "max_retries": max_retries}
        self.use_cache = use_cache
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Initialize browser
        self._browser = Browser()
        logger.info("Initialized BrowserTool")
    
    def get_functions(self) -> Dict[str, Any]:
        """Get the functions provided by this tool with their schemas."""
        return {
            "web_search": {
                "name": "web_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Number of results to return (optional)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                },
                "function": self.search
            },
            "browse": {
                "name": "browse",
                "description": "Browse a webpage and extract its content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to browse"
                        },
                        "instructions": {
                            "type": "string",
                            "description": "Optional instructions for what information to extract"
                        }
                    },
                    "required": ["url"]
                },
                "function": self.browse
            }
        }
    
    def browse(self, url: str, instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Browse a webpage and extract information based on instructions.
        
        Args:
            url: The URL to browse
            instructions: Optional instructions for what information to extract
            
        Returns:
            Dictionary containing the extracted information
        """
        try:
            # Apply retry logic
            for attempt in range(self.browse_config["max_retries"]):
                try:
                    result = self._browser.browse(url, instructions)
                    logger.info(f"Successfully browsed {url}")
                    return {
                        "success": True,
                        "url": url,
                        "content": result
                    }
                except Exception as e:
                    if attempt == self.browse_config["max_retries"] - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1} for {url}: {e}")
        except Exception as e:
            logger.error(f"Error browsing {url}: {e}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    def search(self, query: str, num_results: Optional[int] = None) -> Dict[str, Any]:
        """
        Search the web for information.
        
        Args:
            query: The search query
            num_results: Number of results to return (default: from config)
            
        Returns:
            Dictionary containing the search results
        """
        try:
            # Apply retry logic
            for attempt in range(self.max_retries):
                try:
                    results = self._browser.search(query, num_results or self.search_config["max_results"])
                    logger.info(f"Successfully searched for '{query}'")
                    return {
                        "success": True,
                        "query": query,
                        "results": results,
                        "num_results": len(results)
                    }
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1} for query '{query}': {e}")
        except Exception as e:
            logger.error(f"Error searching for '{query}': {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e)
            }
    
    def extract_text(self, url: str, selector: str) -> Dict[str, Any]:
        """
        Extract text from a webpage using a CSS selector.
        
        Args:
            url: The URL to extract text from
            selector: CSS selector for the elements to extract
            
        Returns:
            Dictionary containing the extracted text
        """
        try:
            # Apply retry logic
            for attempt in range(self.max_retries):
                try:
                    text = self._browser.extract_text(url, selector)
                    logger.info(f"Successfully extracted text from {url}")
                    return {
                        "success": True,
                        "url": url,
                        "selector": selector,
                        "text": text
                    }
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1} for {url}: {e}")
        except Exception as e:
            logger.error(f"Error extracting text from {url}: {e}")
            return {
                "success": False,
                "url": url,
                "selector": selector,
                "error": str(e)
            }
    
    def click_and_extract(self, url: str, click_selector: str, extract_selector: str) -> Dict[str, Any]:
        """
        Click an element and extract text from the resulting page.
        
        Args:
            url: The URL to interact with
            click_selector: CSS selector for the element to click
            extract_selector: CSS selector for the elements to extract after clicking
            
        Returns:
            Dictionary containing the extracted text
        """
        try:
            # Apply retry logic
            for attempt in range(self.max_retries):
                try:
                    text = self._browser.click_and_extract(url, click_selector, extract_selector)
                    logger.info(f"Successfully clicked and extracted from {url}")
                    return {
                        "success": True,
                        "url": url,
                        "click_selector": click_selector,
                        "extract_selector": extract_selector,
                        "text": text
                    }
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise
                    logger.warning(f"Retry {attempt + 1} for {url}: {e}")
        except Exception as e:
            logger.error(f"Error in click and extract on {url}: {e}")
            return {
                "success": False,
                "url": url,
                "click_selector": click_selector,
                "extract_selector": extract_selector,
                "error": str(e)
            }
