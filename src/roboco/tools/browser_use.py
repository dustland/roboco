"""
Browser Use Tool

This module provides a tool for web browsing and task automation,
designed to be compatible with autogen's function calling mechanism.

Dependencies:
- browser-use: For browser automation capabilities
- openai: For some potential LLM integration (optional)
- beautifulsoup4: For better HTML parsing (optional)

Install with:
pip install browser-use openai beautifulsoup4
"""

from typing import Dict, Any, List, Optional, TypeVar, Generic
import asyncio
import traceback
import time
import os
import json
import logging
import tempfile
import uuid
import platform
import subprocess
from loguru import logger
from pydantic import BaseModel, Field

# Required packages
BROWSER_USE_AVAILABLE = False
OPENAI_AVAILABLE = False

# Try to import browser-use package
try:
    from browser_use import Agent, Controller
    from browser_use.browser.browser import Browser as BrowserUseBrowser, BrowserConfig
    from browser_use.browser.context import BrowserContext, BrowserContextConfig
    from browser_use.dom.service import DomService
    from browser_use.controller import browser_utils
    BROWSER_USE_AVAILABLE = True
except ImportError:
    logger.error(
        "browser-use package not found. "
        "Please install it with `pip install browser-use`"
    )

# Try to import OpenAI for potential LLM integration
try:
    import openai
    from langchain_openai import ChatOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI package not found. Some advanced features may not work.")

# Make sure browser-use is available
if not BROWSER_USE_AVAILABLE:
    raise ImportError(
        "Required dependency 'browser-use' not found. "
        "Please install missing dependencies with: pip install browser-use openai"
    )

from roboco.core.tool import Tool
from roboco.core.config import load_config, get_llm_config
from roboco.core.logger import get_logger

# Import browser utils for Chrome detection
try:
    from roboco.utils.browser_utils import get_chrome_path, get_platform, is_chrome_installed
except ImportError:
    logger.error("roboco.utils.browser_utils not found. This is a critical dependency.")
    raise ImportError("Required module roboco.utils.browser_utils not found. Check your installation.")

logger = get_logger(__name__)

# Define context type variable
Context = TypeVar('Context')

class ToolResult(BaseModel):
    """Result of a tool operation."""
    output: Optional[str] = None
    error: Optional[str] = None
    base64_image: Optional[str] = None

class BrowserUseResult(BaseModel):
    """The result of using the browser to perform a task."""
    extracted_content: List[str] = Field(default_factory=list)
    final_result: Optional[str] = None

class BrowserUseTool(Generic[Context], Tool):
    """A tool for browser automation with robust error handling and state management."""

    def __init__(
        self,
        *,
        llm_config: Optional[Dict[str, Any]] = None,
        browser_config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
        **kwargs
    ):
        """Initialize the BrowserUseTool.
        
        Args:
            llm_config: LLM configuration dictionary.
            browser_config: Browser configuration dictionary.
            config_path: Path to configuration file.
            **kwargs: Additional keyword arguments.
        """
        if not BROWSER_USE_AVAILABLE:
            logger.error("browser-use package not available. Please install it with `pip install browser-use`")
            return

        # Initialize state variables
        self.tool_context = None  # Will store the generic context
        
        # Load LLM config from config file if not provided
        if llm_config is None and config_path:
            config = load_config(config_path)
            llm_config = get_llm_config(config)
            logger.debug(f"Loaded llm_config for BrowserUseTool: {llm_config}")
        
        self.llm_config = llm_config or {}
        self.browser_config = browser_config or {}
        
        # Try to detect Chrome browser path if not provided
        if "chrome_instance_path" not in self.browser_config:
            if is_chrome_installed():
                chrome_path = get_chrome_path()
                if chrome_path:
                    self.browser_config["chrome_instance_path"] = chrome_path
                    logger.info(f"Using detected Chrome at: {chrome_path}")
                    logger.info(f"Platform detected: {get_platform()}")
            else:
                logger.warning("Chrome browser not detected. Will use default browser.")
        
        # Initialize the browser when needed (lazy initialization)
        super().__init__(
            name="browser_use",
            description="Use the browser to perform web tasks like navigation, interaction, data extraction, and more.",
            func_or_tool=self.browser_use,
            **kwargs
        )
        
        logger.info("Initialized BrowserUseTool")

    async def browser_use(self, task: str) -> BrowserUseResult:
        """Use the browser to perform a task.
        
        Args:
            task: Description of the task to perform.
            
        Returns:
            BrowserUseResult: Result of the browser operation.
        """
        try:
            # Get OpenAI model from config
            llm = None
            if OPENAI_AVAILABLE and "model" in self.llm_config:
                model_name = self.llm_config.get("model", "gpt-3.5-turbo")
                llm = ChatOpenAI(model=model_name)
                logger.info(f"Using ChatOpenAI with model: {model_name}")
            
            if not llm:
                # We can't continue without an LLM
                logger.error("No LLM configuration available for browser-use Agent")
                return BrowserUseResult(
                    final_result=f"Error: No LLM configuration available for browser-use. Please configure an LLM."
                )
            
            # Log chrome path if available (as information only)
            if "chrome_instance_path" in self.browser_config:
                chrome_path = self.browser_config.get("chrome_instance_path")
                logger.info(f"Chrome path hint (not directly used): {chrome_path}")
            
            # Create an Agent with the task
            logger.info(f"Creating browser agent for task: {task}")
            
            # Agent requires task and llm as required parameters
            agent = Agent(
                task=task,
                llm=llm,
            )
            
            # Run the agent to perform the task
            logger.info("Running browser agent")
            result = await agent.run()
            logger.info("Browser agent completed task")
            
            # Process the result
            if isinstance(result, dict):
                # Extract any content and format the result
                extracted = result.get("content", [])
                if isinstance(extracted, str):
                    extracted = [extracted]
                elif not isinstance(extracted, list):
                    extracted = []
                
                # Format the final result
                final_result = result.get("result", str(result))
                
                return BrowserUseResult(
                    extracted_content=extracted,
                    final_result=final_result
                )
            else:
                # Simple string result
                return BrowserUseResult(
                    final_result=str(result)
                )
            
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"Error in browser_use: {e}\n{tb}")
            return BrowserUseResult(
                final_result=f"Error: {str(e)}"
            )
    
    async def cleanup(self):
        """Clean up browser resources."""
        # Nothing to clean up since we don't keep any browser instances
        pass
    
    def __del__(self):
        """Ensure cleanup when object is destroyed."""
        # Nothing to clean up since we don't keep any browser instances
        pass
    
    @classmethod
    def create_with_context(cls, context: Context) -> "BrowserUseTool[Context]":
        """Factory method to create a BrowserUseTool with a specific context."""
        tool = cls()
        tool.tool_context = context
        return tool 