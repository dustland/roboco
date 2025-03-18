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

# Add current directory to path to find browser_driver.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    # Then import roboco components
    from roboco.core import Agent, load_config
    from roboco.agents.human_proxy import HumanProxy
    from roboco.tools.browser_use import BrowserUseTool
    
except ImportError as e:
    # Use standard logging if imports fail
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.error(f"Error importing modules: {e}")
    logger.info("Make sure roboco and playwright are installed and accessible in your Python path")
    sys.exit(1)

def main(headless=False, use_local=False):
    """Run the web surf example with a basic team using WebKit.
    
    Args:
        headless: Whether to run the browser in headless mode
        use_local: Whether to use the local HTML file instead of example.com
    """
    logger.info("Starting web surf example with WebKit browser")
    
    try:
        # Create WebKit browser instance
        logger.info("Creating WebKit browser instance directly")
        webkit_browser = WebKitBrowser(
            headless=headless,
            disable_security=True,
            slow_mo=200  # Add some delay for WebKit for better visibility
        )
        
        # Load configuration
        config = load_config()
        
        # Create assistant agent
        assistant = Agent(
            name="WebAssistant",
            system_message="""You are a helpful AI assistant that can browse the web.
            When asked to visit a website, you will use the browser_use tool to navigate to the site 
            and extract relevant information.
            """
        )
        
        # Create human proxy agent
        user_proxy = HumanProxy(
            name="User",
            human_input_mode="TERMINATE",  # Only ask for human input when terminating the conversation
            system_message="You can interact with the assistant and execute functions on its behalf."
        )
        
        # Create BrowserUseTool with the WebKit browser instance
        browser_tool = BrowserUseTool(
            browser=webkit_browser,  # Pass our WebKit browser directly
            agent_kwargs={"max_steps": 5}
        )
        
        # Register the tool with both agents
        browser_tool.register_with_agents(caller_agent=assistant, executor_agent=user_proxy)
        
        # Determine which URL to visit
        if use_local:
            # Use the local HTML file
            script_dir = pathlib.Path(__file__).parent.absolute()
            html_path = script_dir / "index.html"
            
            if not html_path.exists():
                logger.error(f"Local HTML file not found: {html_path}")
                logger.info("Create index.html in the examples/web_surf directory or use --real flag")
                return
                
            url = f"file://{html_path}"
            task = "Visit the local test page and tell me what headlines you see."
        else:
            # Use example.com
            url = "https://example.com"
            task = "Visit the website and summarize what you see on the page."
        
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
    parser = argparse.ArgumentParser(description="Web Surf example with WebKit")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--local", action="store_true", help="Use local HTML file instead of example.com")
    
    args = parser.parse_args()
    
    try:
        main(
            headless=args.headless,
            use_local=args.local
        )
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nExiting web surf example")
