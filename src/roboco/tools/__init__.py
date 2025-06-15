"""
Roboco Built-in Tools - Opinionated Best-in-Class Integrations

Built-in tools with our opinionated choices:
- Web: Firecrawl (content extraction) + browser-use (AI automation)
- Search: SERP API for reliable web search
- Memory: Mem0 for intelligent memory management
- Basic: File operations, calculations, etc.
"""

from ..core.tool import Tool, tool

from .basic_tools import BasicTool
# from .web_search import WebSearchTool

def register_builtin_tools():
    """
    Register all built-in tools for general use.
    This makes them available to be assigned to agents in YAML configs.
    """
    register_tool(BasicTool())
    # register_tool(WebSearchTool())


# Export tool classes for direct use if needed
__all__ = [
    "BasicTool",
    # "WebSearchTool",
    "register_builtin_tools"
] 