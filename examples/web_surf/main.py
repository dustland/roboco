#!/usr/bin/env python3
"""
Web Surf Example

This example demonstrates how to use the BrowserTool with Roboco agents
for web browsing and content extraction.
"""

import os
import sys
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import Roboco components
from roboco.agents.human_proxy import HumanProxy
from roboco.core.agent import Agent
from roboco.tools.browser import BrowserTool


def main():
    """Run the web surf example."""
    # Set up logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")
    
    # Create an assistant agent
    assistant = Agent(
        name="Assistant",
        system_message="You are a helpful assistant who can browse the web. You can navigate to URLs, extract text from webpages, and search for information. Use the browse function to visit websites, extract_text to get content from specific elements, and search to find information.",
        terminate_msg="TERMINATE",
        llm_config={
            "config_list": [{"model": "gpt-4"}],
            "temperature": 0.7,
        }
    )
    
    # Create a human proxy agent for both user interaction and function execution
    user_proxy = HumanProxy(
        name="User",
        human_input_mode="NEVER",  # Only prompt for input when terminating
        terminate_msg="TERMINATE",
        system_message="You can interact with the assistant and execute functions on its behalf."
    )
    
    # Create and register the BrowserTool
    logger.debug("Creating and registering BrowserTool")
    browser_tool = BrowserTool(
        max_retries=3,
        timeout=30
    )
    
    # Register BrowserTool with both agents using the register_with_agents method
    browser_tool.register_with_agents(caller_agent=assistant, executor_agent=user_proxy)
    
    logger.debug("BrowserTool registered successfully")
    
    # Test if the browse function is available
    try:
        logger.debug("Testing if browse function is available")
        if hasattr(user_proxy, "_function_map") and "browse" in user_proxy._function_map:
            logger.debug("Browse function found in user_proxy._function_map")
            
            # Test direct execution
            try:
                # Use the __call__ method instead of browse method
                result = browser_tool(url="https://example.com")
                logger.debug(f"Direct browse function call result: {result}")
            except Exception as e:
                logger.error(f"Error executing browse function: {e}")
        else:
            logger.warning("browse function not found in user_proxy._function_map")
    except Exception as e:
        logger.error(f"Error testing browse function: {e}")
    
    # Start a chat with the agent
    print("\nStarting chat with Assistant agent...")
    
    user_proxy.initiate_chat(
        assistant,
        message="Please visit https://www.example.com and tell me what the page is about. Then, search for information about humanoid robotics and summarize your findings."
    )


if __name__ == "__main__":
    main() 