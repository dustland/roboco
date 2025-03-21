"""
Genesis Agent Chat Example

This example demonstrates how to use the GenesisAgent with a HumanProxy in a chat,
where the HumanProxy executes the tools.

IMPORTANT: Before running this script, you need to start the Genesis MCP server manually.
The Genesis MCP server needs to be running and accessible. 

To set up the Genesis environment:

1. Install the MCP package:
   pip install mcp

2. Start the MCP server in a separate terminal with your server file:
   mcp dev server.py
   
   This should display a message like "MCP server listening"

3. Run this example script to interact with the server:
   python genesis_chat.py
   
The GenesisAgent will connect to the running MCP server and provide access to 
physics simulation capabilities through the HumanProxy.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.agents import GenesisAgent
from roboco.core.agent import HumanProxy

async def main():
    """Demo of GenesisAgent with HumanProxy in a chat."""
    
    print("Creating agents for Genesis chat...")
    
    # Create the human proxy agent
    human_proxy = HumanProxy(
        name="User",
        system_message="You are a user interested in physics simulations.",
        human_input_mode="ALWAYS"
    )
    
    # Create the Genesis agent with the human proxy as the executor
    # Use the full command string as used in the terminal
    genesis_agent = GenesisAgent(
        name="GenesisAssistant",
        system_message="You are a physics simulation expert that helps users create and run simulations.",
        mcp_server_command="uv",  # Command to connect to the MCP server
        mcp_server_args=["--directory", "../genesis-mcp", "run", "server.py"],  # Add any additional arguments
        executor_agent=human_proxy  # Set the human_proxy as the executor for the tools
    )
    
    try:
        # Initialize the connection to the MCP server
        print("Initializing connection to MCP server...")
        success = await genesis_agent.initialize()
        if not success:
            print("Failed to connect to MCP server")
            print("\nMake sure you have:")
            print("1. Installed the MCP package: pip install mcp")
            print("2. Started the MCP server in a separate terminal: mcp dev server.py")
            return
        
        print("\n----- Starting chat with Genesis assistant -----")
        print("Type 'exit' to end the conversation")
        
        # Let the human proxy initiate the chat with the Genesis agent
        initial_message = "Hello, I'd like to learn about physics simulations. Can you help me?"
        await human_proxy.initiate_chat(
            recipient=genesis_agent,
            message=initial_message,
            max_turns=10  # Limit the conversation to 10 turns
        )
        
    except Exception as e:
        print(f"Error in Genesis chat demo: {e}")
    finally:
        # Clean up
        print("Closing connection to MCP server...")
        await genesis_agent.close()
        print("\nDemo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 