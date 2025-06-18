#!/usr/bin/env python3
"""
Tool Chat Example - Demonstrates using built-in search and custom weather tools
"""

import asyncio
import sys
from pathlib import Path
import litellm

# Add the src directory to Python path
# This allows importing agentx module from the source code
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from agentx import start_task
from weather_tool import WeatherTool


async def main():
    """Main function to run the tool chat example."""
    print("🔧 Tool Chat Example")
    print("This example uses built-in search tools and a custom weather tool.")
    print("-" * 60)
    
    # Check if DeepSeek supports function calling
    model_name = "deepseek/deepseek-chat"
    supports_fc = litellm.supports_function_calling(model=model_name)
    print(f"🔍 Function calling support for {model_name}: {supports_fc}")
    
    # Use a default test question to avoid manual input during testing
    user_prompt = "what is the weather in shanghai tomorrow?"
    print(f"Test question: {user_prompt}")
    print()

    config_path = Path(__file__).parent / "config" / "team.yaml"
    
    try:
        # Start task and get executor
        task = start_task(user_prompt, config_path)
        
        # Register custom weather tool
        weather_tool = WeatherTool()
        task.register_tool(weather_tool)
        
        # Debug: Check what tools are registered
        print(f"🔧 Registered tools: {task.tool_manager.list_tools()}")
        
        # Get the agent to check tool schemas
        agent = list(task.task.agents.values())[0]
        tool_schemas = agent.get_tools_json()
        print(f"🔧 Agent has access to {len(tool_schemas)} tools")
        
        print(f"🎬 Processing: {user_prompt}")
        print()
        
        # Execute the task with streaming
        async for result in task.step(stream=True):
            chunk_type = result.get("type", "unknown")
            
            if chunk_type == "content":
                print(result.get("content", ""), end="", flush=True)
            elif chunk_type == "tool_call":
                print(f"\n🔧 Calling tool: {result.get('name')}")
                args = result.get('arguments', '')
                if args:
                    print(f"   Arguments: {args}")
            elif chunk_type == "tool_result":
                success = result.get("success", True)
                name = result.get("name", "unknown")
                content = result.get("content", "")
                if success:
                    print(f"\n✅ Tool {name} completed")
                else:
                    print(f"\n❌ Tool {name} failed: {content}")
            elif chunk_type == "tool_calls_start":
                count = result.get("count", 0)
                print(f"\n🔧 Executing {count} tool(s)...")
            elif chunk_type == "routing_decision":
                action = result.get("action")
                if action == "COMPLETE":
                    print(f"\n🎉 Task completed!")
                elif action == "HANDOFF":
                    from_agent = result.get("current_agent")
                    to_agent = result.get("next_agent")
                    print(f"\n🔄 Handoff from {from_agent} to {to_agent}")
            elif chunk_type == "error":
                print(f"\n❌ Error: {result.get('content', 'Unknown error')}")
            elif chunk_type == "warning":
                print(f"\n⚠️ Warning: {result.get('content', 'Unknown warning')}")
            # Ignore other chunk types silently
        
        print("\n" + "=" * 60)
        print("✅ Task completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 