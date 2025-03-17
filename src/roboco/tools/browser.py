"""
Browser Tool

This module provides a tool for web browsing and page interaction,
designed to be compatible with autogen's function calling mechanism.
"""

from typing import Dict, Any, List, Optional, ClassVar
from loguru import logger
from browser_use import Browser

from roboco.core.tool import Tool

class BrowserTool(Tool):
    """Tool for web browsing and information extraction."""
    
    # Class-level browser instance
    _browser: ClassVar[Browser] = Browser()
    
    # Default configurations
    default_browse_config: ClassVar[Dict[str, Any]] = {"timeout": 30, "max_retries": 3}
    default_max_retries: ClassVar[int] = 3
    default_timeout: ClassVar[int] = 30
    
    def __init__(
        self,
        browse: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        max_retries: int = 3,
        timeout: int = 30,
        **kwargs
    ):
        """Initialize the browser tool.
        
        Args:
            browse: Browse-specific settings
            use_cache: Whether to use caching
            max_retries: Maximum number of retry attempts
            timeout: Operation timeout in seconds
            **kwargs: Additional arguments to pass to the Tool parent class
        """
        # Store configuration in instance variables
        self.browse_config = browse or self.default_browse_config
        self.use_cache = use_cache
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Define the browse function
        def browse(url: str, instructions: Optional[str] = None) -> Dict[str, Any]:
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
                for attempt in range(self.max_retries):
                    try:
                        # Navigate to the URL
                        context = self._browser.new_context()
                        page = context.new_page()
                        page.goto(url, timeout=self.timeout * 1000)
                        
                        # Extract page content
                        content = page.content()
                        title = page.title()
                        
                        logger.info(f"Successfully browsed {url}")
                        return {
                            "success": True,
                            "url": url,
                            "title": title,
                            "content": content[:1000] + "..." if len(content) > 1000 else content
                        }
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            raise
                        logger.warning(f"Retry {attempt + 1} for {url}: {e}")
            except Exception as e:
                logger.error(f"Error browsing {url}: {e}")
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }
        
        # Define the extract_text function
        def extract_text(url: str, selector: str) -> Dict[str, Any]:
            """
            Extract text content from a webpage using a CSS selector.
            
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
                        # Navigate to the URL
                        context = self._browser.new_context()
                        page = context.new_page()
                        page.goto(url, timeout=self.timeout * 1000)
                        
                        # Extract text using the selector
                        elements = page.query_selector_all(selector)
                        texts = [element.text_content() for element in elements]
                        
                        logger.info(f"Successfully extracted text from {url} using selector '{selector}'")
                        return {
                            "success": True,
                            "url": url,
                            "selector": selector,
                            "texts": texts,
                            "count": len(texts)
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
        
        # Define the search function
        def search(query: str, max_results: int = 5) -> Dict[str, Any]:
            """
            Search the web for information.
            
            Args:
                query: The search query
                max_results: Maximum number of results to return
                
            Returns:
                Dictionary containing search results
            """
            try:
                # Apply retry logic
                for attempt in range(self.max_retries):
                    try:
                        # Perform search using the browser
                        results = self._browser.search(query, max_results=max_results)
                        
                        logger.info(f"Successfully searched for '{query}'")
                        return {
                            "success": True,
                            "query": query,
                            "results": results,
                            "count": len(results)
                        }
                    except Exception as e:
                        if attempt == self.max_retries - 1:
                            raise
                        logger.warning(f"Retry {attempt + 1} for search '{query}': {e}")
            except Exception as e:
                logger.error(f"Error searching for '{query}': {e}")
                return {
                    "success": False,
                    "query": query,
                    "error": str(e)
                }
        
        # Initialize the Tool parent class with the browse function
        super().__init__(
            name="browse",
            description="Browse a webpage and extract information",
            func_or_tool=browse,
            **kwargs
        )
        
        logger.info("Initialized BrowserTool")
