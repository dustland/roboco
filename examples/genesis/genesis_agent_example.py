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

from roboco.core import GenesisAgent

async def main():
    """Demo of GenesisAgent with MCP server."""
    
    print("Creating Genesis agent...")
    agent = GenesisAgent(
        name="GenesisAssistant",
        system_message="You are a physics simulation expert that helps users create and run simulations.",
    )
    
    try:
        # Get information about Genesis World
        print("\n----- Genesis World Overview -----")
        overview = await agent.get_world_info("overview")
        print(f"{overview}\n")
        
        print("----- Genesis World Capabilities -----")
        capabilities = await agent.get_world_info("capabilities")
        print(f"{capabilities}\n")
        
        # Get a basic simulation prompt
        print("----- Basic Simulation Template -----")
        sim_code = await agent.get_basic_simulation(world_size=20, agent_count=5)
        print(f"{sim_code}\n")
        
        # Run the simulation
        print("----- Running Simulation -----")
        result = await agent.run_simulation(sim_code)
        
        if result.get("success"):
            print("\nSimulation logs:")
            for log in result.get("logs", []):
                print(f"  {log}")
                
            print("\nSimulation results:")
            pprint(result.get("results", {}))
        else:
            print(f"Simulation failed: {result.get('message')}")
            
    except Exception as e:
        print(f"Error in Genesis agent demo: {e}")
    finally:
        # Clean up
        await agent.close()
        print("\nDemo completed!")

if __name__ == "__main__":
    asyncio.run(main())