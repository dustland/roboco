"""
Web Tools - Opinionated web automation and content extraction.

Built-in integrations:
- Firecrawl: Superior web content extraction (replaces Jina)
- browser-use: AI-first browser automation (better than Playwright for agents)
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebContent:
    """Extracted web content."""
    url: str
    title: str
    content: str
    markdown: str
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


@dataclass
class BrowserAction:
    """Browser automation action result."""
    action: str
    success: bool
    result: Any
    screenshot: Optional[str] = None
    error: Optional[str] = None


class FirecrawlTool:
    """
    Firecrawl integration for superior web content extraction.
    
    Why Firecrawl over Jina:
    - Better content extraction quality
    - Handles JavaScript-heavy sites
    - Built-in markdown conversion
    - Rate limiting and reliability
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize Firecrawl client."""
        try:
            from firecrawl import FirecrawlApp
            
            if not self.api_key:
                import os
                self.api_key = os.getenv("FIRECRAWL_API_KEY")
            
            if self.api_key:
                self._client = FirecrawlApp(api_key=self.api_key)
                logger.info("Firecrawl client initialized")
            else:
                logger.warning("Firecrawl API key not found. Set FIRECRAWL_API_KEY environment variable.")
                
        except ImportError:
            logger.warning("Firecrawl not installed. Install with: pip install firecrawl-py")
        except Exception as e:
            logger.error(f"Failed to initialize Firecrawl: {e}")
    
    async def extract_content(self, url: str, options: Optional[Dict[str, Any]] = None) -> WebContent:
        """Extract content from a URL using Firecrawl."""
        if not self._client:
            return WebContent(
                url=url,
                title="",
                content="",
                markdown="",
                metadata={},
                success=False,
                error="Firecrawl client not available"
            )
        
        try:
            # Default options for better extraction
            crawl_options = {
                "formats": ["markdown", "html"],
                "includeTags": ["title", "meta"],
                "excludeTags": ["nav", "footer", "aside"],
                "waitFor": 2000,  # Wait for JS to load
                **(options or {})
            }
            
            result = self._client.scrape_url(url, crawl_options)
            
            if result.get("success"):
                data = result.get("data", {})
                
                return WebContent(
                    url=url,
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    markdown=data.get("markdown", ""),
                    metadata=data.get("metadata", {}),
                    success=True
                )
            else:
                return WebContent(
                    url=url,
                    title="",
                    content="",
                    markdown="",
                    metadata={},
                    success=False,
                    error=result.get("error", "Unknown error")
                )
                
        except Exception as e:
            logger.error(f"Firecrawl extraction failed for {url}: {e}")
            return WebContent(
                url=url,
                title="",
                content="",
                markdown="",
                metadata={},
                success=False,
                error=str(e)
            )
    
    async def crawl_site(self, url: str, options: Optional[Dict[str, Any]] = None) -> List[WebContent]:
        """Crawl multiple pages from a site."""
        if not self._client:
            return []
        
        try:
            crawl_options = {
                "limit": 10,
                "formats": ["markdown"],
                "excludePaths": ["/admin", "/login"],
                **(options or {})
            }
            
            result = self._client.crawl_url(url, crawl_options)
            
            if result.get("success"):
                pages = result.get("data", [])
                return [
                    WebContent(
                        url=page.get("url", ""),
                        title=page.get("title", ""),
                        content=page.get("content", ""),
                        markdown=page.get("markdown", ""),
                        metadata=page.get("metadata", {}),
                        success=True
                    )
                    for page in pages
                ]
            else:
                logger.error(f"Crawl failed: {result.get('error')}")
                return []
                
        except Exception as e:
            logger.error(f"Site crawl failed for {url}: {e}")
            return []


class BrowserUseTool:
    """
    browser-use integration for AI-first browser automation.
    
    Why browser-use over Playwright:
    - AI-first design for LLM agents
    - Natural language control ("click login button")
    - Self-healing when page layouts change
    - Built for autonomous operation
    - Less brittle than selector-based automation
    """
    
    def __init__(self):
        self._browser = None
        self._page = None
        self._init_browser()
    
    def _init_browser(self):
        """Initialize browser-use."""
        try:
            from browser_use import Browser
            
            self._browser = Browser()
            logger.info("browser-use initialized")
            
        except ImportError:
            logger.warning("browser-use not installed. Install with: pip install browser-use")
        except Exception as e:
            logger.error(f"Failed to initialize browser-use: {e}")
    
    async def start_session(self) -> bool:
        """Start a browser session."""
        if not self._browser:
            return False
        
        try:
            await self._browser.start()
            self._page = await self._browser.new_page()
            logger.info("Browser session started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start browser session: {e}")
            return False
    
    async def navigate(self, url: str) -> BrowserAction:
        """Navigate to a URL."""
        if not self._page:
            await self.start_session()
        
        try:
            await self._page.goto(url)
            
            return BrowserAction(
                action=f"navigate_to_{url}",
                success=True,
                result={"url": url, "title": await self._page.title()}
            )
            
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return BrowserAction(
                action=f"navigate_to_{url}",
                success=False,
                result=None,
                error=str(e)
            )
    
    async def ai_action(self, instruction: str) -> BrowserAction:
        """
        Perform an action using natural language.
        
        Examples:
        - "Click the login button"
        - "Fill in the email field with user@example.com"
        - "Scroll down to find more content"
        - "Take a screenshot of the current page"
        """
        if not self._page:
            await self.start_session()
        
        try:
            # This would use browser-use's AI capabilities
            # For now, return a placeholder
            result = await self._page.ai_action(instruction)
            
            return BrowserAction(
                action=instruction,
                success=True,
                result=result
            )
            
        except Exception as e:
            logger.error(f"AI action failed: {e}")
            return BrowserAction(
                action=instruction,
                success=False,
                result=None,
                error=str(e)
            )
    
    async def extract_data(self, instruction: str) -> BrowserAction:
        """
        Extract data using natural language.
        
        Examples:
        - "Get all product names and prices"
        - "Extract the main article content"
        - "Find all email addresses on this page"
        """
        if not self._page:
            await self.start_session()
        
        try:
            # This would use browser-use's AI extraction
            data = await self._page.extract_data(instruction)
            
            return BrowserAction(
                action=f"extract_{instruction}",
                success=True,
                result=data
            )
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return BrowserAction(
                action=f"extract_{instruction}",
                success=False,
                result=None,
                error=str(e)
            )
    
    async def screenshot(self, full_page: bool = False) -> BrowserAction:
        """Take a screenshot."""
        if not self._page:
            await self.start_session()
        
        try:
            screenshot_data = await self._page.screenshot(full_page=full_page)
            
            return BrowserAction(
                action="screenshot",
                success=True,
                result={"screenshot": screenshot_data},
                screenshot=screenshot_data
            )
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return BrowserAction(
                action="screenshot",
                success=False,
                result=None,
                error=str(e)
            )
    
    async def close(self):
        """Close the browser session."""
        if self._browser:
            try:
                await self._browser.close()
                logger.info("Browser session closed")
            except Exception as e:
                logger.error(f"Failed to close browser: {e}")


# Convenience functions for easy use
async def extract_web_content(url: str, api_key: Optional[str] = None) -> WebContent:
    """Extract content from a URL using Firecrawl."""
    tool = FirecrawlTool(api_key)
    return await tool.extract_content(url)


async def crawl_website(url: str, limit: int = 10, api_key: Optional[str] = None) -> List[WebContent]:
    """Crawl a website using Firecrawl."""
    tool = FirecrawlTool(api_key)
    return await tool.crawl_site(url, {"limit": limit})


async def automate_browser(instruction: str) -> BrowserAction:
    """Perform browser automation using natural language."""
    tool = BrowserUseTool()
    await tool.start_session()
    try:
        return await tool.ai_action(instruction)
    finally:
        await tool.close()


# Tool registration helpers
def register_web_tools(agent: "Agent"):
    """Register all web tools with an agent."""
    from ..core.tool import register_function
    
    # Register Firecrawl functions
    register_function(agent, extract_web_content, "extract_web_content", 
                     "Extract clean content from any URL using Firecrawl")
    
    register_function(agent, crawl_website, "crawl_website",
                     "Crawl multiple pages from a website")
    
    # Register browser automation
    register_function(agent, automate_browser, "automate_browser",
                     "Automate browser actions using natural language")
    
    logger.info(f"Registered web tools for agent {agent.name}")


# Export main classes and functions
__all__ = [
    "FirecrawlTool",
    "BrowserUseTool", 
    "WebContent",
    "BrowserAction",
    "extract_web_content",
    "crawl_website",
    "automate_browser",
    "register_web_tools"
] 