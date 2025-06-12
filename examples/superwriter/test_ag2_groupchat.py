#!/usr/bin/env python3
"""
AG2 GroupChat Tool Execution Test

This script tests AG2 tool execution using GroupChat pattern.
"""

import os
import yaml
from autogen import ConversableAgent, GroupChat, GroupChatManager, register_function
from roboco.memory.manager import MemoryManager
from roboco.builtin_tools.memory_tools import create_memory_tools
from roboco.tool import create_tool_function_for_ag2

def test_ag2_groupchat():
    """Test AG2 tool execution using GroupChat pattern."""
    print("🧪 Testing AG2 GroupChat Tool Execution")
    print("=" * 50)
    
    try:
        # Load config
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        # Create memory manager
        memory_manager = MemoryManager(config.get('memory', {}))
        print("✅ Memory manager created")
        
        # Create agents
        planner = ConversableAgent(
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
        
        executor = ConversableAgent(
            name="executor",
            system_message="I execute tools for other agents.",
            llm_config=False,
            human_input_mode="NEVER"
        )
        
        print("✅ Agents created")
        
        # Register memory tools
        memory_tools = create_memory_tools(memory_manager)
        for memory_tool in memory_tools:
            tool_function = create_tool_function_for_ag2(memory_tool)
            register_function(
                tool_function,
                caller=planner,
                executor=executor,
                name=memory_tool.name,
                description=memory_tool.description
            )
        
        print(f"✅ Registered {len(memory_tools)} memory tools")
        
        # Create GroupChat
        group_chat = GroupChat(
            agents=[planner, executor],
            messages=[],
            max_round=5
        )
        
        # Create GroupChatManager
        manager = GroupChatManager(
            groupchat=group_chat,
            llm_config=planner.llm_config
        )
        
        print("✅ GroupChat setup complete")
        
        # Test conversation
        print("\n🚀 Starting GroupChat conversation...")
        
        chat_result = planner.initiate_chat(
            recipient=manager,
            message="Please use add_memory to store this: 'Tesla analysis requirements: market position and competitive advantages'",
            clear_history=True
        )
        
        print("✅ Chat completed")
        print(f"📝 Chat result: {chat_result}")
        
        # Check chat history
        print(f"\n💬 Chat History ({len(group_chat.messages)} messages):")
        for i, msg in enumerate(group_chat.messages, 1):
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

if __name__ == "__main__":
    success = test_ag2_groupchat()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}") 