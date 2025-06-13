"""
Search Tools - Decorator-based implementation using the new Tool system.
"""

import os
import httpx
from typing import Annotated, Optional
from roboco.tool.base import Tool, tool

# Global search manager instance
_search_manager = None

def set_search_manager(manager):
    """Set the global search manager instance."""
    global _search_manager
    _search_manager = manager

def get_search_manager():
    """Get the global search manager instance."""
    return _search_manager

class SearchTool(Tool):
    """Search and web content extraction tools using the new decorator-based system."""
    
    def __init__(self, search_manager=None):
        super().__init__()
        self.search_manager = search_manager or get_search_manager()
    
    @tool(name="web_search", description="Search the web for information on any topic using multiple search engines")
    async def web_search(
        self,
        task_id: str,
        agent_id: str,
        query: Annotated[str, "Search query to find information"],
        max_results: Annotated[int, "Maximum number of results to return"] = 10
    ) -> str:
        """Search the web for information using configured search engines."""
        try:
            if not self.search_manager:
                return "❌ Search system not configured. Please set up a search manager."
            
            # Perform the search
            results = await self.search_manager.search(query, max_results=max_results)
            
            if not results:
                return f"🔍 No results found for query: '{query}'"
            
            # Format results for display
            formatted_results = []
            for i, result in enumerate(results[:max_results], 1):
                title = result.get('title', 'No title')
                url = result.get('url', 'No URL')
                snippet = result.get('snippet', result.get('description', 'No description'))
                
                # Truncate long snippets
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                
                formatted_results.append(f"{i}. **{title}**\n   {snippet}\n   🔗 {url}")
            
            return f"🔍 Found {len(results)} results for '{query}':\n\n" + "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"❌ Search failed: {str(e)}"
    
    @tool(name="extract_url", description="Extract and clean content from a URL using Jina Reader API")
    async def extract_url(
        self,
        task_id: str,
        agent_id: str,
        url: Annotated[str, "The URL to extract content from"],
        max_length: Annotated[int, "Maximum length of extracted content in characters"] = 8000
    ) -> str:
        """Extract and clean content from a URL using Jina Reader API."""
        try:
            # Use Jina Reader API to extract clean content
            jina_url = f"https://r.jina.ai/{url}"
            
            # Prepare headers with API key if available
            headers = {}
            
            # Try to get Jina API key from environment
            jina_api_key = os.getenv("JINA_API_KEY")
            if jina_api_key:
                headers["Authorization"] = f"Bearer {jina_api_key}"
                print(f"🔑 Using Jina API key for higher rate limits")
            else:
                print(f"ℹ️ No JINA_API_KEY found, using free tier (lower rate limits)")
            
            # Make request to Jina Reader
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(jina_url, headers=headers)
                response.raise_for_status()
                
                content = response.text
                
                # Truncate if too long
                if len(content) > max_length:
                    content = content[:max_length] + "\n\n[Content truncated...]"
                
                return f"📄 Extracted content from {url}:\n\n{content}"
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                return f"❌ Rate limit exceeded. Please try again later or set JINA_API_KEY for higher limits."
            elif e.response.status_code == 404:
                return f"❌ URL not found or cannot be accessed: {url}"
            else:
                return f"❌ HTTP error {e.response.status_code}: {e.response.text}"
        except httpx.TimeoutException:
            return f"❌ Request timed out while extracting content from {url}"
        except Exception as e:
            return f"❌ Failed to extract content: {str(e)}"

# Create a default instance for backward compatibility
def create_search_tool(search_manager=None):
    """Create a search tool instance."""
    return SearchTool(search_manager)

# Export the tool class
__all__ = ['SearchTool', 'create_search_tool', 'set_search_manager', 'get_search_manager']

