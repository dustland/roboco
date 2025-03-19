"""
Browser Use Tool

This module provides a tool for web browsing and task automation.
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
from pydantic import BaseModel, Field

import browser_use
from browser_use import Agent
from langchain_openai import ChatOpenAI

from roboco.core.tool import Tool
from roboco.core.logger import get_logger
from roboco.utils.browser_utils import get_chrome_path, is_chrome_installed

logger = get_logger(__name__)

# Define context type variable
Context = TypeVar('Context')

class BrowserUseResult(BaseModel):
    """The result of using the browser to perform a task."""
    extracted_content: List[str] = Field(default_factory=list)
    final_result: Optional[str] = None

class BrowserUseTool(Generic[Context], Tool):
    """A tool for browser automation."""

    def __init__(
        self,
        *,
        llm_config: Optional[Any] = None,
        browser_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize the BrowserUseTool."""
        self.tool_context = None
        self.llm_config = llm_config or {}
        self.browser_config = browser_config or {}
        
        # Auto-detect Chrome path if not provided
        if "chrome_instance_path" not in self.browser_config and is_chrome_installed():
            chrome_path = get_chrome_path()
            if chrome_path:
                self.browser_config["chrome_instance_path"] = chrome_path
                logger.info(f"Using Chrome at: {chrome_path}")
        
        super().__init__(
            name="browser_use",
            description="Use the browser to perform web tasks like navigation, interaction, data extraction, and more.",
            func_or_tool=self.browser_use,
            **kwargs
        )
        
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
            
            # Import necessary classes for browser creation
            from browser_use.browser.browser import Browser, BrowserConfig
            
            # Create browser with Chrome configuration
            browser_options = BrowserConfig(
                headless=self.browser_config.get("headless", False),
                chrome_instance_path=self.browser_config.get("chrome_instance_path"),
                disable_security=self.browser_config.get("disable_security", True),
                extra_chromium_args=["--no-sandbox", "--disable-dev-shm-usage", "--user-data-dir=./user_data"]
            )
            
            # Initialize browser
            browser = Browser(config=browser_options)
            
            # Create agent with browser
            agent = Agent(
                task=task,
                llm=llm,
                browser=browser
            )
            
            # Run agent
            logger.info(f"Running browser agent for task: {task}")
            result = await agent.run()
            
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
            return BrowserUseResult(final_result=f"Error: {str(e)}")
    
    @classmethod
    def create_with_context(cls, context: Context) -> "BrowserUseTool[Context]":
        """Create a BrowserUseTool with a specific context."""
        tool = cls()
        tool.tool_context = context
        return tool 