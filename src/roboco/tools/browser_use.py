"""
Browser Use Tool

This module provides a tool for web browsing and task automation.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

import browser_use
from browser_use import Agent, BrowserContextConfig
from browser_use.browser.browser import Browser, BrowserConfig
from langchain_openai import ChatOpenAI

from roboco.core.tool import Tool
from roboco.core.logger import get_logger
from roboco.utils.browser_utils import get_chrome_path, get_platform, is_chrome_installed

import os

logger = get_logger(__name__)

# Define context type variable
Context = TypeVar('Context')

class BrowserUseResult(BaseModel):
    """The result of using the browser to perform a task."""
    extracted_content: List[str] = Field(default_factory=list)
    final_result: Optional[str] = None

class BrowserUseTool(Generic[Context], Tool):
    """Browser automation tool using the browser_use library.
    
    Features:
    - Web browsing, interaction, and data extraction
    - Chrome detection and configuration
    - Customizable output location for session recordings
    
    Examples:
        # Basic usage
        browser_tool = BrowserUseTool(llm_config={"model": "gpt-4o"})
        
        # With custom output directory
        browser_tool = BrowserUseTool(
            llm_config={"model": "gpt-4o"},
            output_dir="./browser_sessions"  # GIF saved as "./browser_sessions/agent_history.gif"
        )
    """

    def __init__(
        self,
        *,
        llm_config: Optional[Any] = None,
        browser_config: Optional[Dict[str, Any]] = None,
        output_dir: Optional[str] = None,
        **kwargs
    ):
        """Initialize the BrowserUseTool.
        
        Args:
            llm_config: LLM configuration
            browser_config: Browser configuration
            output_dir: Directory for saving agent_history.gif
        """
        self.tool_context = None
        self.llm_config = llm_config or {}
        self.browser_config = browser_config or {}
        self.browser = None
        self.agent = None
        self.output_dir = output_dir
        
        # Standard browser setup
        if not is_chrome_installed():
            logger.warning("Google Chrome is not installed on this system.")
            logger.warning("Browser automation may not work properly.")
        
        # Get Chrome path based on platform if not provided
        if "chrome_instance_path" not in self.browser_config and is_chrome_installed():
            chrome_path = get_chrome_path()
            if chrome_path:
                self.browser_config["chrome_instance_path"] = chrome_path
                logger.info(f"Detected platform: {get_platform()}")
                logger.info(f"Using Chrome at: {chrome_path}")
                
        if "new_context_config" not in self.browser_config:
            new_context_config = BrowserContextConfig(
                wait_between_actions=1,
                browser_window_size={
                    "width": 1280,
                    "height": 1100
                },
                highlight_elements=True,
            )
            self.browser_config["new_context_config"] = new_context_config
        
        super().__init__(
            name="browser_use",
            description="Use the browser to perform web tasks like navigation, interaction, data extraction, and more.",
            func_or_tool=self.browser_use,
            **kwargs
        )
    
    async def _initialize_browser(self):
        """Initialize the browser if not already done."""
        if self.browser is None:
            # Create browser configuration
            browser_options = BrowserConfig(
                headless=self.browser_config.get("headless", False),
                chrome_instance_path=self.browser_config.get("chrome_instance_path"),
                disable_security=self.browser_config.get("disable_security", True),
            )
            
            # Create and store the browser instance
            self.browser = Browser(config=browser_options)
            logger.info("Browser initialized")
        
    async def browser_use(self, task: str) -> BrowserUseResult:
        """Use the browser to perform a task."""
        try:
            # Create LLM from config
            if hasattr(self.llm_config, 'model'):
                # Pydantic model config
                llm = ChatOpenAI(
                    model=self.llm_config.model,
                    temperature=getattr(self.llm_config, 'temperature', 0.7),
                    max_tokens=getattr(self.llm_config, 'max_tokens', 500),
                    api_key=getattr(self.llm_config, 'api_key', None),
                    base_url=getattr(self.llm_config, 'base_url', None)
                )
            else:
                # Dictionary config
                llm = ChatOpenAI(**self.llm_config)
            
            # Initialize browser if needed
            await self._initialize_browser()
            
            # Set up output path for GIF if directory is specified
            if self.output_dir:
                os.makedirs(self.output_dir, exist_ok=True)
                gif_output = os.path.join(self.output_dir, "agent_history.gif")
                logger.info(f"Browser session will be recorded to: {gif_output}")
            else:
                gif_output = True  # Just enable GIF generation with default path
            
            # Create a new agent for each task with the shared browser
            self.agent = Agent(
                task=task,
                llm=llm,
                browser=self.browser,
                generate_gif=gif_output  # Pass the full path when output_dir is specified
            )
            
            # Run agent
            logger.info(f"Running browser agent for task: {task}")
            result = await self.agent.run()
            
            # Process the result
            if isinstance(result, dict):
                extracted = result.get("content", [])
                if isinstance(extracted, str):
                    extracted = [extracted]
                elif not isinstance(extracted, list):
                    extracted = []
                    
                final_result = result.get("result", str(result))
                
                return BrowserUseResult(
                    extracted_content=extracted,
                    final_result=final_result
                )
            else:
                return BrowserUseResult(final_result=str(result))
            
        except Exception as e:
            logger.error(f"Browser use error: {e}")
            # Try to reinitialize browser if there was an error
            if "Browser.new_context: Target page, context or browser has been closed" in str(e):
                logger.info("Attempting to reinitialize browser after closure")
                self.browser = None
                await self._initialize_browser()
                return BrowserUseResult(
                    final_result=f"Browser was reset due to error: {str(e)}. Please try your task again."
                )
            return BrowserUseResult(final_result=f"Error: {str(e)}")
    
    async def cleanup(self):
        """Close the browser and release resources."""
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
                self.agent = None
                logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    @classmethod
    def create_with_context(cls, context: Context) -> "BrowserUseTool[Context]":
        """Create a BrowserUseTool with a specific context."""
        tool = cls()
        tool.tool_context = context
        return tool 