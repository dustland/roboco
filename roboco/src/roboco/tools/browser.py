"""
Browser Tool

This module provides a tool for web browsing and page interaction,
designed to be compatible with autogen's function calling mechanism.
"""

import asyncio
from typing import Dict, Any, List, Optional
from loguru import logger
from browser_use import Agent as BrowserAgent
from langchain_openai import ChatOpenAI

from roboco.core.config import load_config_from_file
from roboco.core.tool import Tool

class BrowserUseTool(Tool):
    """Tool for browsing web pages and interacting with their content using browser-use package."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the browser tool with browser-use package.
        
        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(name="browser", description="Browse websites and interact with web content")
        
        # Load config for LLM
        if config_path:
            self.config = load_config_from_file(config_path)
        else:
            self.config = {}
        
        logger.info("Initialized BrowserUseTool using browser-use package")
    
    def browse(self, task: str) -> Dict[str, Any]:
        """
        Execute a browser task using the browser-use Agent.
        
        Args:
            task: Description of the task to perform in the browser
            
        Returns:
            Dictionary with task results
        """
        try:
            # Create a synchronous wrapper around the async browser-use Agent
            result = asyncio.run(self._run_browser_task(task))
            logger.info(f"Completed browser task: {task}")
            return {
                "success": True,
                "task": task,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error performing browser task '{task}': {str(e)}")
            return {
                "success": False,
                "task": task,
                "error": str(e)
            }
    
    async def _run_browser_task(self, task: str) -> Dict[str, Any]:
        """
        Run a browser task asynchronously using the browser-use Agent.
        
        Args:
            task: Description of the task to perform
            
        Returns:
            Result of the browser task
        """
        # Use our config to determine the model for the browser agent
        llm_config = self.config.get("llm", {})
        model_name = llm_config.get("model", "gpt-4o")
        
        # Create a browser-use Agent with the specified task
        browser_agent = BrowserAgent(
            task=task,
            llm=ChatOpenAI(model=model_name),
        )
        
        # Run the task and return the result
        result = await browser_agent.run()
        return result
