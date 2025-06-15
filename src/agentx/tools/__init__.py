"""
AgentX Built-in Tools - Opinionated Best-in-Class Integrations

Built-in tools with our opinionated choices:
- Web: Firecrawl (content extraction) + browser-use (AI automation)
- Search: SERP API for reliable web search
- Memory: Mem0 for intelligent memory management
- Basic: File operations, calculations, etc.
"""

from ..core.tool import Tool, tool, register_tool
from ..utils.logger import get_logger

from .basic_tools import BasicTool

logger = get_logger(__name__)

def register_builtin_tools():
    """
    Register all built-in tools for general use.
    This makes them available to be assigned to agents in YAML configs.
    """
    # Always register basic tools
    register_tool(BasicTool())
    logger.info("Registered BasicTool")
    
    # Register search tools if dependencies are available
    try:
        from .search_tools import SearchTool
        register_tool(SearchTool())
        logger.info("Registered SearchTool")
    except ImportError as e:
        logger.warning(f"SearchTool not available: {e}")
    except Exception as e:
        logger.error(f"Failed to register SearchTool: {e}")
        raise
    
    # Register web tools if dependencies are available
    try:
        from .web_tools import WebTool
        register_tool(WebTool())
        logger.info("Registered WebTool")
    except ImportError as e:
        logger.warning(f"WebTool not available: {e}")
    except Exception as e:
        logger.error(f"Failed to register WebTool: {e}")
        raise


# Export tool classes for direct use if needed
__all__ = [
    "BasicTool",
    # "WebSearchTool",
    "register_builtin_tools"
] 