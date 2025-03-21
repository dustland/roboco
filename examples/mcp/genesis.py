"""
Genesis Agent Example

This example demonstrates how to use the GenesisAgent to interact with
the Genesis MCP server for physics simulations.
"""

import asyncio
import os
import sys
from pprint import pprint
from pathlib import Path

# Add the project root to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.agents import GenesisAgent

async def main():
    """Demo of GenesisAgent with MCP server."""
    
    print("Creating Genesis agent...")
    
    # Configure the transport to use stdio with the genesis-mcp command
    transport_config = {
        "type": "stdio",
        "command": "genesis-mcp",
        "args": []
    }
    
    # Alternatively, to use a remote server with SSE transport:
    # transport_config = {
    #     "type": "sse", 
    #     "url": "https://your-genesis-server.example.com/sse",
    #     "auth_token": "your-auth-token"  # Optional
    # }
    
    # Create the agent
    agent = GenesisAgent(
        name="GenesisAssistant",
        system_message="You are a physics simulation expert that helps users create and run simulations.",
        transport_config=transport_config
    )
    
    try:
        # Initialize the connection to the MCP server
        print("Initializing connection to Genesis MCP server...")
        success = await agent.initialize()
        if not success:
            print("Failed to connect to Genesis MCP server")
            return

        # Get information about Genesis World
        print("\n----- Genesis World Information -----")
        world_info = await agent.send_command("get_world_info")
        if world_info.get("success"):
            print("World information retrieved successfully:")
            pprint(world_info.get("result", {}))
        else:
            print(f"Failed to get world information: {world_info.get('message')}")
        print()
        
        # Get a basic simulation template
        print("----- Basic Simulation Template -----")
        content, success = await agent.get_resource("basic_simulation")
        if success and content:
            print(f"Template retrieved ({len(content)} characters)")
            print(f"First 100 characters: {content[:100]}...\n")
            sim_code = content
        else:
            print("Failed to get template")
            return
        
        # Run the simulation
        print("----- Running Simulation -----")
        result = await agent.send_command("run_simulation", {
            "code": sim_code,
            "parameters": {}
        })
        
        if result.get("success"):
            print("\nSimulation executed successfully:")
            pprint(result.get("result", {}))
        else:
            print(f"Simulation failed: {result.get('message')}")
            
    except Exception as e:
        print(f"Error in Genesis agent demo: {e}")
    finally:
        # Clean up
        print("Closing connection to Genesis MCP server...")
        await agent.close()
        print("\nDemo completed!")

if __name__ == "__main__":
    asyncio.run(main()) 