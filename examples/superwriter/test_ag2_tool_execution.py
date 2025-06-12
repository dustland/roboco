#!/usr/bin/env python3
"""
AG2 Tool Execution Test

This script tests proper AG2 tool execution patterns to fix our remaining issue.
"""

import asyncio
import os
import yaml
from roboco.core.agents import Agent
from roboco.memory.manager import MemoryManager
from roboco.builtin_tools.memory_tools import create_memory_tools
from roboco.tool import create_tool_function_for_ag2
from autogen import register_function

async def test_ag2_tool_execution():
    """Test proper AG2 tool execution pattern."""
    print("🧪 Testing AG2 Tool Execution")
    print("=" * 50)
    
    try:
        # Load config
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        # Create memory manager
        memory_manager = MemoryManager(config.get('memory', {}))
        print("✅ Memory manager created")
        
        # Create caller agent (the one that will call tools)
        caller = Agent(
            name="planner",
            system_message="You are a helpful planner. When asked to do something, use the memory tools to store your work. Always use add_memory to store important information.",
            llm_config={
                "config_list": [
                    {
                        "model": "gpt-4o-mini",
                        "api_key": os.getenv("OPENAI_API_KEY")
                    }
                ]
            }
        )
        print("✅ Caller agent created")
        
        # Create executor agent (the one that will execute tools)
        executor = Agent(
            name="executor",
            system_message="I execute tools for other agents.",
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
                caller=caller,
                executor=executor,
                name=memory_tool.name,
                description=memory_tool.description
            )
        
        print(f"✅ Registered {len(memory_tools)} memory tools")
        
        # Test conversation with tool execution
        print("\n🚀 Testing conversation with tool execution...")
        
        # Start a conversation between caller and executor
        chat_result = caller.initiate_chat(
            recipient=executor,
            message="Please use add_memory to store this: 'Tesla analysis requirements: market position and competitive advantages'",
            max_turns=3,
            clear_history=True
        )
        
        print(f"✅ Chat completed")
        print(f"📝 Chat result: {chat_result}")
        
        # Check chat history
        if hasattr(chat_result, 'chat_history'):
            print(f"\n💬 Chat History ({len(chat_result.chat_history)} messages):")
            for i, msg in enumerate(chat_result.chat_history, 1):
                sender = msg.get('name', 'Unknown')
                content = msg.get('content', '')[:200] + "..." if len(msg.get('content', '')) > 200 else msg.get('content', '')
                print(f"   {i}. {sender}: {content}")
        
        # Check if memory was actually added
        print(f"\n🧠 Checking memory storage...")
        memories = memory_manager.search_memories("Tesla")
        print(f"   Found {len(memories)} memories containing 'Tesla'")
        for memory in memories:
            print(f"   - {memory.get('content', '')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the AG2 tool execution test."""
    print("🎯 AG2 Tool Execution Test")
    print("=" * 60)
    
    success = await test_ag2_tool_execution()
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ AG2 tool execution test completed")
    else:
        print("❌ AG2 tool execution test failed")

if __name__ == "__main__":
    asyncio.run(main()) 