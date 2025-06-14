"""
Roboco Built-in Tools - Opinionated Best-in-Class Integrations

Built-in tools with our opinionated choices:
- Web: Firecrawl (content extraction) + browser-use (AI automation)
- Search: SERP API for reliable web search
- Memory: Mem0 for intelligent memory management
- Basic: File operations, calculations, etc.
"""

from .memory_tools import MemoryTool
from .basic_tools import BasicTool
from .search_tools import SearchTool
from .web_tools import (
    FirecrawlTool, 
    BrowserUseTool, 
    WebContent, 
    BrowserAction,
    extract_web_content,
    crawl_website,
    automate_browser,
    register_web_tools
)

__all__ = [
    # Traditional tools
    'MemoryTool',
    'BasicTool', 
    'SearchTool',
    
    # Opinionated Web Tools (Best-in-Class)
    'FirecrawlTool',        # Superior content extraction
    'BrowserUseTool',       # AI-first browser automation
    'WebContent',           # Content data structure
    'BrowserAction',        # Action result structure
    
    # Convenience functions
    'extract_web_content',  # Quick content extraction
    'crawl_website',        # Site crawling
    'automate_browser',     # Natural language browser control
    'register_web_tools',   # Register all web tools
] 