#!/usr/bin/env python3
"""
Tool Chat Example - Demonstrates using built-in search and custom weather tools
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
# This allows importing agentx module from the source code
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentx import create_task, register_tool
from weather_tool import WeatherTool


async def main():
    """Run the tool chat example."""
    print("🔧 Tool Chat Example")
    print("This example uses built-in search tools and a custom weather tool.")
    print("-" * 60)
    
    # Register the custom tool before starting the task
    print("🌤️  Registering custom weather tool...")
    register_tool(WeatherTool())
    print("✅ Custom weather tool registered")

    # Get user input
    try:
        user_prompt = input("Enter your question: ")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting.")
        return

    print(f"\n🎬 Processing: {user_prompt}\n")
    
    config_path = "config/team.yaml"

    try:
        # Create and execute task
        task = create_task(config_path)
        
        # Execute with streaming
        async for update in task.execute_task(user_prompt, stream=True):
            update_type = update.get("type")
            
            if update_type == "content":
                print(update["content"], end="", flush=True)
            elif update_type == "info":
                # Print informational updates from the task loop
                print(f'\x1b[33m{update["content"]}\x1b[0m', end="", flush=True)
            elif update_type == "routing_decision":
                if update["action"] == "complete":
                    print(f"\n\n🎉 Task completed!")
                    break
        
        print(f"\n\n✅ Tool chat finished!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 