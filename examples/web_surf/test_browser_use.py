import os
import asyncio
import sys
import logging
from dotenv import load_dotenv
import time

from roboco.core import load_config
from roboco.tools.browser_use import BrowserUseTool
# Import our utility to check for Chrome
from roboco.utils.browser_utils import get_chrome_path, get_platform, is_chrome_installed

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_browser_use")

load_dotenv()

config = load_config()

# Check if Chrome is installed
if not is_chrome_installed():
    print("Error: Google Chrome is not installed on this system.")
    print("Please install Google Chrome and try again.")
    sys.exit(1)

# Get Chrome path based on platform
chrome_path = get_chrome_path()
logger.info(f"Detected platform: {get_platform()}")
logger.info(f"Using Chrome at: {chrome_path}")

async def test_with_browser_use_tool():
    """Test the BrowserUseTool with a simple task."""
    # Configure browser with platform-specific Chrome path
    browser_config = {
        "headless": False,
        "chrome_instance_path": chrome_path,
        "disable_security": True,
        "window_size": {"width": 1280, "height": 900}
    }
    
    # Create BrowserUseTool instance
    browser_tool = BrowserUseTool(browser_config=browser_config)
    
    try:
        # Use the browser to navigate to example.com
        result = await browser_tool.browser_use("Go to example.com")
        logger.info(f"Result: {result.final_result}")
        
        # Wait a moment to see the result
        await asyncio.sleep(2)
        
        # Take a screenshot
        result = await browser_tool.browser_use("Take a screenshot")
        logger.info(f"Screenshot taken: {result.final_result}")
        
        # Extract content
        result = await browser_tool.browser_use("Extract content from the page")
        logger.info(f"Extracted content: {result.final_result[:100]}...")
        
        # Clean up will happen automatically through the __del__ method
        await asyncio.sleep(3)  # Wait to see results
        
        return "Test passed successfully"
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        return f"Test failed with error: {e}"

if __name__ == "__main__":
    result = asyncio.run(test_with_browser_use_tool())
    logger.info(result)
