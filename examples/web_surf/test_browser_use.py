import os
import asyncio
import sys
import logging

from roboco.core import load_config
from roboco.tools.browser_use import BrowserUseTool
from roboco.utils.browser_utils import get_chrome_path, get_platform, is_chrome_installed

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_browser_use")

# Load environment variables and configuration
config = load_config()

if not is_chrome_installed():
    logger.error("Google Chrome is not installed on this system.")
    logger.error("Please install Google Chrome and try again.")
    sys.exit(1)

# Get Chrome path based on platform
chrome_path = get_chrome_path()
logger.info(f"Detected platform: {get_platform()}")
logger.info(f"Using Chrome at: {chrome_path}")

async def test_with_browser_use_tool():
    """Test the BrowserUseTool with a simple task."""
    # Configure browser 
    browser_config = {
        "headless": False,
        "chrome_instance_path": chrome_path,
        "disable_security": True,
        "window_size": {"width": 1280, "height": 900}
    }
    
    # Create BrowserUseTool instance with configurations
    browser_tool = BrowserUseTool(
        browser_config=browser_config,
        llm_config=config.llm
    )
    
    try:
        # Use the browser to navigate to example.com
        logger.info("Step 1: Navigating to example.com")
        result = await browser_tool.browser_use("Go to tiwater.com")
        logger.info(f"Result: {result.final_result}")
        
        # Wait a moment to see the result
        await asyncio.sleep(3)
        
        # Extract content
        logger.info("Step 2: Extracting content from the page")
        result = await browser_tool.browser_use("Extract and summarize content from this webpage")
        
        if result.extracted_content:
            logger.info(f"Extracted content: {result.extracted_content[0][:100]}...")
        
        logger.info(f"Final result: {result.final_result[:100]}...")
        
        # Wait to see results
        await asyncio.sleep(3)
        
        return "Test completed successfully"
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        return f"Test failed with error: {e}"

if __name__ == "__main__":
    result = asyncio.run(test_with_browser_use_tool())
    logger.info(result)
