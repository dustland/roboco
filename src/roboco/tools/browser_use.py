"""
Browser Use Tool

This module provides a tool for web browsing and task automation.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field
import json

import browser_use
from browser_use import Agent, BrowserContextConfig
from browser_use.browser.browser import Browser, BrowserConfig as BrowserUseLibConfig
from langchain_openai import ChatOpenAI

from roboco.core.tool import Tool, command
from loguru import logger
from roboco.core.models import ToolConfig
from roboco.utils.browser_utils import get_chrome_path, get_platform, is_chrome_installed

import os

logger = logger.bind(module=__name__)

# Define context type variable
Context = TypeVar('Context')

class BrowserUseConfig(ToolConfig):
    """Configuration for BrowserUseTool."""
    llm_model: str = Field(
        default="gpt-4o",
        description="LLM model to use with browser-use"
    )
    llm_temperature: float = Field(
        default=0.0,
        description="Temperature for LLM inference"
    )
    browser_path: Optional[str] = Field(
        default=None,
        description="Path to the Chrome/Chromium browser executable"
    )
    headless: bool = Field(
        default=True,
        description="Whether to run the browser in headless mode"
    )
    output_dir: Optional[str] = Field(
        default="./output/browser",
        description="Directory for browser output and screenshots"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    max_steps: int = Field(
        default=15,
        description="Maximum number of steps in browser automation"
    )

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
        config: Optional[BrowserUseConfig] = None,
        **kwargs
    ):
        """Initialize the BrowserUseTool.

        Args:
            config: Configuration for the browser tool
            **kwargs: Additional keyword arguments
        """
        # First extract tool name and description from kwargs to prevent them from being passed twice
        name = kwargs.pop("name", "browser_use")
        description = kwargs.pop("description", "Use the browser to perform web tasks like navigation, interaction, data extraction, and more.")
        
        # Initialize with config
        if config is None:
            config = BrowserUseConfig()
        elif isinstance(config, dict):
            config = BrowserUseConfig(**config)
            
        self.logger = logger.bind(module=__name__)
        
        # Configure LLM
        self.llm_config = {
            "model": config.llm_model,
            "temperature": config.llm_temperature
        }
        
        # Configure browser
        browser_path = config.browser_path or get_chrome_path()
        if not browser_path:
            if not is_chrome_installed():
                self.logger.warning("Chrome/Chromium not found. Browser tool may not work correctly.")
                browser_path = ""
            else:
                self.logger.warning("Chrome/Chromium path not detected automatically. Using default.")
        
        # Create browser config without browser_path parameter
        self.browser_config = BrowserUseLibConfig(
            headless=config.headless
        )
        
        # Add chrome path to chrome_instance_path if available
        if browser_path:
            self.browser_config.chrome_instance_path = browser_path
        
        # Set output directory
        self.output_dir = config.output_dir
        if self.output_dir:
            os.makedirs(self.output_dir, exist_ok=True)
        
        # Additional settings
        self.debug = config.debug
        self.max_steps = config.max_steps
        
        # Browser instance will be initialized on demand
        self.browser = None
        self.agent = None
        
        # Standard browser setup
        if not is_chrome_installed():
            logger.warning("Google Chrome is not installed on this system.")
            logger.warning("Browser automation may not work properly.")
        
        # Get Chrome path based on platform if not provided
        if not hasattr(self.browser_config, 'chrome_instance_path') and is_chrome_installed():
            chrome_path = get_chrome_path()
            if chrome_path:
                self.browser_config.chrome_instance_path = chrome_path
                logger.info(f"Detected platform: {get_platform()}")
                logger.info(f"Using Chrome at: {chrome_path}")
                
        if not hasattr(self.browser_config, 'new_context_config'):
            new_context_config = BrowserContextConfig(
                wait_between_actions=1,
                browser_window_size={
                    "width": 1280,
                    "height": 1100
                },
                highlight_elements=True,
            )
            self.browser_config.new_context_config = new_context_config
        
        # Create a synchronous wrapper for the async browser_use function
        def sync_browser_use(*args, **kwargs):
            import asyncio
            return asyncio.run(self.browser_use(*args, **kwargs))
        
        # Now initialize the Tool parent class
        super().__init__(
            name=name,
            description=description,
            **kwargs
        )
    
    async def _initialize_browser(self):
        """Initialize the browser if it hasn't been initialized yet."""
        if self.browser is None:
            # Create browser instance
            self.browser = Browser(self.browser_config)
            
            # Create LLM (ChatOpenAI) for the agent
            llm = ChatOpenAI(
                model=self.llm_config.get("model", "gpt-4o"),
                temperature=self.llm_config.get("temperature", 0.0)
            )
            
            # Initialize the browser-use agent
            self.agent = Agent(
                llm=llm,
                browser=self.browser,
                output_dir=self.output_dir,
                max_iterations=self.max_steps
            )
            
            self.logger.info("Browser and agent initialized successfully")
            
        return self.browser
    
    @command()
    def browser_use(self, task: str) -> Dict[str, Any]:
        """Use the browser to perform a task.
        
        Args:
            task: The task to perform with the browser.
            
        Returns:
            A dictionary containing the extracted content and final result.
        """
        import asyncio
        
        # Track original content and final result
        result = {
            "extracted_content": [],
            "final_result": None
        }
        
        self.logger.info(f"Running browser task: {task}")
        
        try:
            # Get the current event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the browser task in the event loop
            agent_result = loop.run_until_complete(self._run_browser_task(task))
            
            # Extract observations from agent steps
            if agent_result.steps:
                for step in agent_result.steps:
                    if step.observation:
                        result["extracted_content"].append(step.observation)
            
            # Store final result
            result["final_result"] = agent_result.output
            
            if self.debug and self.output_dir:
                # Save debug information
                self.logger.info(f"Saving browser session debug information to {self.output_dir}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing browser task: {e}")
            result["final_result"] = f"Error: {str(e)}"
            return result
    
    async def _run_browser_task(self, task: str):
        """Run the browser task asynchronously."""
        await self._initialize_browser()
        return await self.agent.run(task=task)
    
    async def cleanup(self):
        """Clean up browser resources when done."""
        if self.browser:
            try:
                await self.browser.close()
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {e}")
            finally:
                self.browser = None
                self.agent = None
    
    @classmethod
    def create_with_config(cls, config: Optional[Dict[str, Any]] = None) -> "BrowserUseTool":
        """Create a new instance of the BrowserUseTool with the given configuration.
        
        Args:
            config: Configuration for the tool.
            
        Returns:
            A new BrowserUseTool instance.
        """
        if config is None:
            config = {}
        return cls(config=BrowserUseConfig(**config)) 