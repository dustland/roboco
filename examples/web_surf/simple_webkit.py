#!/usr/bin/env python3
"""
Simple test script for using browser_use with Chromium.
"""

import os
import asyncio
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

async def test_browser_use():
    """
    Test browser_use with Chromium browser.
    """
    try:
        # Import required modules
        from browser_use import Agent, Browser, Controller
        from browser_use.browser.browser import BrowserConfig
        from browser_use.browser.context import BrowserContextConfig
        from langchain_openai import ChatOpenAI
        
        # Use a more reliable URL for testing
        url = "https://www.google.com"
        logger.info(f"Testing browser_use with Chromium on: {url}")
        
        # Get API key from environment
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.error("No OPENAI_API_KEY environment variable found")
            return
        
        # Set up LLM
        llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-4o",
            temperature=0.7
        )
        
        # Create browser config with more robust settings
        browser_config = BrowserConfig(
            headless=False,
            disable_security=True
        )
        
        # Create context config with longer wait times for reliability
        context_config = BrowserContextConfig(
            wait_for_network_idle_page_load_time=5.0,  # Increased wait time
            maximum_wait_page_load_time=10.0,  # Increased maximum wait
            browser_window_size={'width': 1280, 'height': 900},
            highlight_elements=True
        )
        
        # Set context config
        browser_config.new_context_config = context_config
        
        # Create browser and controller
        browser = Browser(config=browser_config)
        controller = Controller()
        
        # Create agent with a simple task
        task = f"Visit {url} and summarize what you see on the homepage."
        logger.info(f"Creating agent with task: {task}")
        
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            controller=controller,
            generate_gif=False
        )
        
        # Run agent with more steps
        logger.info("Running agent...")
        result = await asyncio.wait_for(
            agent.run(max_steps=10),  # Increased from 3 to 10
            timeout=180  # Longer timeout
        )
        
        # Display results
        print("\n" + "="*50)
        print(" Browser-Use with Chromium Results")
        print("="*50)
        
        print(f"\nTask: {task}")
        print(f"URL: {url}")
        
        # Display extracted content
        print("\nExtracted Content:")
        for content in result.extracted_content() or []:
            print(f"- {content}")
            
        # Display final result
        print("\nFinal Result:")
        print(result.final_result() or "No result returned")
        
    except Exception as e:
        logger.error(f"Error testing browser_use: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_browser_use())
