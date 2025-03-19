#!/usr/bin/env python3
"""
Web Surf Example with BrowserUseTool

This example demonstrates how to use the BrowserUseTool for web browsing tasks.
"""

from roboco.core import Agent, get_llm_config
from roboco.agents import HumanProxy
from roboco.tools import BrowserUseTool

def main():
    # Create assistant agent
    assistant = Agent(
        name="WebAssistant",
        terminate_msg="TERMINATE",
        system_message="You are a helpful AI assistant that can browse the web."
    )
    
    # Create human proxy
    user_proxy = HumanProxy(
        name="User",
        terminate_msg="TERMINATE",
        human_input_mode="NEVER"
    )
    
    # Create browser tool with output directory
    browser_tool = BrowserUseTool(
        llm_config=get_llm_config(),
        output_dir="./screenshots"
    )
    
    # Register the tool with agents
    browser_tool.register_with_agents(
        caller_agent=assistant, 
        executor_agent=user_proxy
    )
    
    # Start a conversation
    print(f"Starting conversation. Browser output will be saved to: ./screenshots")
    user_proxy.initiate_chat(
        assistant,
        message="Please visit https://example.com and describe what you see."
    )
    
    print("Example complete")

if __name__ == "__main__":
    main()
