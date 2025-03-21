import asyncio
import os

from roboco.core.config import get_llm_config
from roboco.tools import BrowserUseTool

async def simple_browser_example():
    
    # Set output directory
    output_dir = "workspace/screenshots"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create browser tool with output directory
    browser_tool = BrowserUseTool(
        llm_config=get_llm_config(),
        output_dir=output_dir
    )
    
    # Use the browser to navigate and extract content
    print(f"Running browser task. Output will be saved to: {output_dir}")
    result = await browser_tool.browser_use("Go to example.com and summarize the content")
    print(f"Result: {result.final_result}")
    
    # Clean up
    await browser_tool.cleanup()
    print(f"Browser session recorded to: {os.path.join(output_dir, 'agent_history.gif')}")
    
    return "Done!"

if __name__ == "__main__":
    print("Testing BrowserUseTool with custom output directory")
    result = asyncio.run(simple_browser_example())
    print(result)
