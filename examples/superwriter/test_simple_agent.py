#!/usr/bin/env python3
"""
Simple Agent Test

This script tests a single agent directly to isolate the communication issue.
"""

import asyncio
import os
import yaml
from roboco.core.agents import Agent
from roboco.memory.manager import MemoryManager
from roboco.builtin_tools.memory_tools import create_memory_tools
from roboco.tool import create_tool_function_for_ag2
from autogen import register_function

async def test_simple_agent():
    """Test a single agent directly."""
    print("🧪 Testing Single Agent")
    print("=" * 50)
    
    try:
        # Load config
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        # Create memory manager
        memory_manager = MemoryManager(config.get('memory', {}))
        print("✅ Memory manager created")
        
        # Create a simple agent
        agent = Agent(
            name="test_planner",
            system_message="You are a helpful planner. When asked to do something, use the memory tools to store your work.",
            llm_config={
                "config_list": [
                    {
                        "model": "gpt-4o-mini",
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                ]
            }
        )
        print("✅ Agent created")
        
        # Create executor agent for tools
        executor = Agent(
            name="executor",
            system_message="I execute tools.",
            llm_config=False,  # No LLM needed for executor
            human_input_mode="NEVER"
        )
        print("✅ Executor agent created")
        
        # Register memory tools using proper AG2 pattern
        memory_tools = create_memory_tools(memory_manager)
        for memory_tool in memory_tools:
            tool_function = create_tool_function_for_ag2(memory_tool)
            
            # Use autogen.register_function for proper registration
            register_function(
                tool_function,
                caller=agent,
                executor=executor,
                name=memory_tool.name,
                description=memory_tool.description
            )
        
        print(f"✅ Registered {len(memory_tools)} memory tools")
        
        # Test direct agent response
        print("\n🚀 Testing direct agent response...")
        
        # Create a simple message
        message = "Please use add_memory to store this: 'Tesla analysis requirements: market position and competitive advantages'"
        
        # Get agent response
        response = agent.generate_reply(
            messages=[{"content": message, "role": "user"}]
        )
        
        print(f"✅ Agent response received")
        print(f"📝 Response type: {type(response)}")
        print(f"📝 Response: {response}")
        
        # If response contains tool calls, we need to execute them
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"🔧 Found {len(response.tool_calls)} tool calls")
            for i, tool_call in enumerate(response.tool_calls):
                print(f"   {i+1}. {tool_call.function.name}: {tool_call.function.arguments}")

        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the simple agent test."""
    print("🎯 Simple Agent Test")
    print("=" * 60)
    
    success = await test_simple_agent()
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ Simple agent test completed")
    else:
        print("❌ Simple agent test failed")

if __name__ == "__main__":
    asyncio.run(main()) 