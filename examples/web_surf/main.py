#!/usr/bin/env python3
"""
Web Surf Example with WebKit

This example demonstrates how to use WebKit directly with the roboco framework's BrowserUseTool
in a basic team consisting of a HumanProxy and an Agent.
"""

import os
import sys
import argparse
import pathlib

from roboco.utils.browser_utils import get_chrome_path, get_platform, is_chrome_installed

# Add current directory to path to find browser_driver.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.core.logger import get_logger
logger = get_logger(__name__)

try:
    # Then import roboco components
    from roboco.core import Agent, load_config
    from roboco.agents.human_proxy import HumanProxy
    from roboco.tools.browser_use import BrowserUseTool
    
except ImportError as e:
    # Use standard logging if imports fail
    logger.error(f"Error importing modules: {e}")
    logger.info("Make sure roboco and playwright are installed and accessible in your Python path")
    sys.exit(1)

def main():
    """Run the web surf example with a basic team using WebKit.
    
    Args:
        headless: Whether to run the browser in headless mode
        use_local: Whether to use the local HTML file instead of example.com
    """
    logger.info("Starting web surf example with WebKit browser")
    
    try:
        # Create WebKit browser instance
        config = load_config()
        if not is_chrome_installed():
            logger.error("Google Chrome is not installed on this system.")
            logger.error("Please install Google Chrome and try again.")
            sys.exit(1)

        # Get Chrome path based on platform
        chrome_path = get_chrome_path()
        logger.info(f"Detected platform: {get_platform()}")
        logger.info(f"Using Chrome at: {chrome_path}")
            # Create assistant agent
        assistant = Agent(
            name="WebAssistant",
            terminate_msg="TERMINATE",
            system_message="""You are a helpful AI assistant that can browse the web.
            When asked to visit a website, you will use the browser_use tool to navigate to the site 
            and extract relevant information.
            """
        )
        
        # Create human proxy agent
        user_proxy = HumanProxy(
            name="User",
            terminate_msg="TERMINATE",
            human_input_mode="TERMINATE",  # Only ask for human input when terminating the conversation
            system_message="You can interact with the assistant and execute functions on its behalf."
        )
        
        browser_config = {
            "headless": False,
            "chrome_instance_path": chrome_path,
            "disable_security": True,
            "window_size": {"width": 1280, "height": 900}
        }
        
        # Create BrowserUseTool with the WebKit browser instance
        browser_tool = BrowserUseTool(
            browser_config=browser_config,  # Pass our WebKit browser directly
            llm_config=config.llm
        )
        
        # Register the tool with both agents
        browser_tool.register_with_agents(caller_agent=assistant, executor_agent=user_proxy)
        
        # Use example.com
        url = "https://tiwater.com"
        logger.info(f"Will instruct the assistant to browse to: {url}")
        
        # Start a conversation with the assistant
        user_proxy.initiate_chat(
            assistant,
            message=f"Please visit {url} and describe what you see."
        )
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nExiting web surf example")
