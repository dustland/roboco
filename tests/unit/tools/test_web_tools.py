"""
Tests for web tools functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from roboco.tools.web_tools import (
    WebContent, BrowserAction, FirecrawlTool, BrowserUseTool,
    extract_web_content, crawl_website, automate_browser
)


class TestWebContent:
    """Test WebContent dataclass."""
    
    def test_web_content_creation_success(self):
        """Test WebContent creation for successful extraction."""
        content = WebContent(
            url="https://example.com",
            title="Example Site",
            content="This is the content",
            markdown="# Example Site\nThis is the content",
            metadata={"author": "John Doe"},
            success=True
        )
        
        assert content.url == "https://example.com"
        assert content.title == "Example Site"
        assert content.content == "This is the content"
        assert content.markdown == "# Example Site\nThis is the content"
        assert content.metadata == {"author": "John Doe"}
        assert content.success is True
        assert content.error is None
    
    def test_web_content_creation_failure(self):
        """Test WebContent creation for failed extraction."""
        content = WebContent(
            url="https://example.com",
            title="",
            content="",
            markdown="",
            metadata={},
            success=False,
            error="Connection timeout"
        )
        
        assert content.url == "https://example.com"
        assert content.success is False
        assert content.error == "Connection timeout"


class TestBrowserAction:
    """Test BrowserAction dataclass."""
    
    def test_browser_action_success(self):
        """Test BrowserAction for successful action."""
        action = BrowserAction(
            action="click",
            success=True,
            result={"clicked": True},
            screenshot="base64_image_data"
        )
        
        assert action.action == "click"
        assert action.success is True
        assert action.result == {"clicked": True}
        assert action.screenshot == "base64_image_data"
        assert action.error is None
    
    def test_browser_action_failure(self):
        """Test BrowserAction for failed action."""
        action = BrowserAction(
            action="click",
            success=False,
            result=None,
            error="Element not found"
        )
        
        assert action.action == "click"
        assert action.success is False
        assert action.result is None
        assert action.error == "Element not found"


class TestFirecrawlTool:
    """Test FirecrawlTool class."""
    
    def test_firecrawl_tool_init_with_api_key(self):
        """Test FirecrawlTool initialization with API key."""
        with patch('roboco.tools.web_tools.FirecrawlApp') as mock_firecrawl:
            mock_client = Mock()
            mock_firecrawl.return_value = mock_client
            
            tool = FirecrawlTool(api_key="test_key")
            
            assert tool.api_key == "test_key"
            assert tool._client == mock_client
            mock_firecrawl.assert_called_once_with(api_key="test_key")
    
    def test_firecrawl_tool_init_from_env(self):
        """Test FirecrawlTool initialization from environment variable."""
        with patch('roboco.tools.web_tools.FirecrawlApp') as mock_firecrawl, \
             patch('os.getenv', return_value="env_key"):
            mock_client = Mock()
            mock_firecrawl.return_value = mock_client
            
            tool = FirecrawlTool()
            
            assert tool.api_key == "env_key"
            assert tool._client == mock_client
    
    def test_firecrawl_tool_init_no_api_key(self):
        """Test FirecrawlTool initialization without API key."""
        with patch('roboco.tools.web_tools.FirecrawlApp') as mock_firecrawl, \
             patch('os.getenv', return_value=None):
            
            tool = FirecrawlTool()
            
            assert tool.api_key is None
            assert tool._client is None
            mock_firecrawl.assert_not_called()
    
    def test_firecrawl_tool_init_import_error(self):
        """Test FirecrawlTool initialization with import error."""
        with patch('roboco.tools.web_tools.FirecrawlApp', side_effect=ImportError("Module not found")):
            tool = FirecrawlTool(api_key="test_key")
            
            assert tool._client is None
    
    @pytest.mark.asyncio
    async def test_extract_content_success(self):
        """Test successful content extraction."""
        mock_client = Mock()
        mock_client.scrape_url.return_value = {
            "success": True,
            "data": {
                "title": "Test Page",
                "content": "Test content",
                "markdown": "# Test Page\nTest content",
                "metadata": {"author": "Test Author"}
            }
        }
        
        tool = FirecrawlTool(api_key="test_key")
        tool._client = mock_client
        
        result = await tool.extract_content("https://example.com")
        
        assert result.success is True
        assert result.url == "https://example.com"
        assert result.title == "Test Page"
        assert result.content == "Test content"
        assert result.markdown == "# Test Page\nTest content"
        assert result.metadata == {"author": "Test Author"}
        assert result.error is None
        
        # Verify client was called with correct options
        mock_client.scrape_url.assert_called_once()
        call_args = mock_client.scrape_url.call_args
        assert call_args[0][0] == "https://example.com"
        assert "formats" in call_args[0][1]
        assert "markdown" in call_args[0][1]["formats"]
    
    @pytest.mark.asyncio
    async def test_extract_content_failure(self):
        """Test failed content extraction."""
        mock_client = Mock()
        mock_client.scrape_url.return_value = {
            "success": False,
            "error": "Page not found"
        }
        
        tool = FirecrawlTool(api_key="test_key")
        tool._client = mock_client
        
        result = await tool.extract_content("https://example.com")
        
        assert result.success is False
        assert result.url == "https://example.com"
        assert result.error == "Page not found"
        assert result.title == ""
        assert result.content == ""
    
    @pytest.mark.asyncio
    async def test_extract_content_no_client(self):
        """Test content extraction without client."""
        tool = FirecrawlTool()
        tool._client = None
        
        result = await tool.extract_content("https://example.com")
        
        assert result.success is False
        assert result.error == "Firecrawl client not available"
    
    @pytest.mark.asyncio
    async def test_extract_content_exception(self):
        """Test content extraction with exception."""
        mock_client = Mock()
        mock_client.scrape_url.side_effect = Exception("Network error")
        
        tool = FirecrawlTool(api_key="test_key")
        tool._client = mock_client
        
        result = await tool.extract_content("https://example.com")
        
        assert result.success is False
        assert result.error == "Network error"
    
    @pytest.mark.asyncio
    async def test_extract_content_with_options(self):
        """Test content extraction with custom options."""
        mock_client = Mock()
        mock_client.scrape_url.return_value = {
            "success": True,
            "data": {"title": "Test", "content": "Content", "markdown": "# Test", "metadata": {}}
        }
        
        tool = FirecrawlTool(api_key="test_key")
        tool._client = mock_client
        
        custom_options = {"waitFor": 5000, "excludeTags": ["script"]}
        await tool.extract_content("https://example.com", options=custom_options)
        
        # Verify custom options were merged
        call_args = mock_client.scrape_url.call_args[0][1]
        assert call_args["waitFor"] == 5000
        assert "script" in call_args["excludeTags"]
    
    @pytest.mark.asyncio
    async def test_crawl_site_success(self):
        """Test successful site crawling."""
        mock_client = Mock()
        mock_client.crawl_url.return_value = {
            "success": True,
            "data": [
                {
                    "url": "https://example.com/page1",
                    "title": "Page 1",
                    "content": "Content 1",
                    "markdown": "# Page 1",
                    "metadata": {}
                },
                {
                    "url": "https://example.com/page2",
                    "title": "Page 2",
                    "content": "Content 2",
                    "markdown": "# Page 2",
                    "metadata": {}
                }
            ]
        }
        
        tool = FirecrawlTool(api_key="test_key")
        tool._client = mock_client
        
        results = await tool.crawl_site("https://example.com")
        
        assert len(results) == 2
        assert all(isinstance(result, WebContent) for result in results)
        assert results[0].url == "https://example.com/page1"
        assert results[0].title == "Page 1"
        assert results[1].url == "https://example.com/page2"
        assert results[1].title == "Page 2"
    
    @pytest.mark.asyncio
    async def test_crawl_site_no_client(self):
        """Test site crawling without client."""
        tool = FirecrawlTool()
        tool._client = None
        
        results = await tool.crawl_site("https://example.com")
        
        assert results == []


class TestBrowserUseTool:
    """Test BrowserUseTool class."""
    
    def test_browser_use_tool_init_success(self):
        """Test BrowserUseTool initialization success."""
        with patch('roboco.tools.web_tools.Browser') as mock_browser:
            mock_browser_instance = Mock()
            mock_browser.return_value = mock_browser_instance
            
            tool = BrowserUseTool()
            
            assert tool._browser == mock_browser_instance
            mock_browser.assert_called_once()
    
    def test_browser_use_tool_init_import_error(self):
        """Test BrowserUseTool initialization with import error."""
        with patch('roboco.tools.web_tools.Browser', side_effect=ImportError("Module not found")):
            tool = BrowserUseTool()
            
            assert tool._browser is None
    
    @pytest.mark.asyncio
    async def test_start_session_success(self):
        """Test successful browser session start."""
        mock_browser = AsyncMock()
        mock_browser.start.return_value = True
        
        tool = BrowserUseTool()
        tool._browser = mock_browser
        
        result = await tool.start_session()
        
        assert result is True
        mock_browser.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_session_no_browser(self):
        """Test browser session start without browser."""
        tool = BrowserUseTool()
        tool._browser = None
        
        result = await tool.start_session()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_navigate_success(self):
        """Test successful navigation."""
        mock_browser = AsyncMock()
        mock_browser.navigate.return_value = {"success": True, "url": "https://example.com"}
        
        tool = BrowserUseTool()
        tool._browser = mock_browser
        
        result = await tool.navigate("https://example.com")
        
        assert isinstance(result, BrowserAction)
        assert result.action == "navigate"
        assert result.success is True
        assert result.result["url"] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_ai_action_success(self):
        """Test successful AI action."""
        mock_browser = AsyncMock()
        mock_browser.ai_action.return_value = {"success": True, "action_taken": "clicked button"}
        
        tool = BrowserUseTool()
        tool._browser = mock_browser
        
        result = await tool.ai_action("click the login button")
        
        assert isinstance(result, BrowserAction)
        assert result.action == "ai_action"
        assert result.success is True
        assert "action_taken" in result.result


class TestWebToolsFunctions:
    """Test standalone web tool functions."""
    
    @pytest.mark.asyncio
    async def test_extract_web_content(self):
        """Test extract_web_content function."""
        with patch('roboco.tools.web_tools.FirecrawlTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool_class.return_value = mock_tool
            
            expected_content = WebContent(
                url="https://example.com",
                title="Test",
                content="Content",
                markdown="# Test",
                metadata={},
                success=True
            )
            mock_tool.extract_content = AsyncMock(return_value=expected_content)
            
            result = await extract_web_content("https://example.com", api_key="test_key")
            
            assert result == expected_content
            mock_tool_class.assert_called_once_with(api_key="test_key")
            mock_tool.extract_content.assert_called_once_with("https://example.com")
    
    @pytest.mark.asyncio
    async def test_crawl_website(self):
        """Test crawl_website function."""
        with patch('roboco.tools.web_tools.FirecrawlTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool_class.return_value = mock_tool
            
            expected_results = [
                WebContent("https://example.com/1", "Page 1", "Content 1", "# Page 1", {}, True),
                WebContent("https://example.com/2", "Page 2", "Content 2", "# Page 2", {}, True)
            ]
            mock_tool.crawl_site = AsyncMock(return_value=expected_results)
            
            results = await crawl_website("https://example.com", limit=5, api_key="test_key")
            
            assert results == expected_results
            mock_tool_class.assert_called_once_with(api_key="test_key")
            mock_tool.crawl_site.assert_called_once_with("https://example.com", options={"limit": 5})
    
    @pytest.mark.asyncio
    async def test_automate_browser(self):
        """Test automate_browser function."""
        with patch('roboco.tools.web_tools.BrowserUseTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool_class.return_value = mock_tool
            
            expected_action = BrowserAction(
                action="ai_action",
                success=True,
                result={"completed": True}
            )
            mock_tool.ai_action = AsyncMock(return_value=expected_action)
            
            result = await automate_browser("click the submit button")
            
            assert result == expected_action
            mock_tool_class.assert_called_once()
            mock_tool.ai_action.assert_called_once_with("click the submit button") 