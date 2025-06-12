#!/usr/bin/env python3
"""
Memory Tool Execution Test

This script tests memory tool execution directly to find the bug
causing None return values.
"""

import asyncio
import os
import yaml
from roboco.memory.manager import MemoryManager
from roboco.builtin_tools.memory_tools import create_memory_tools

async def test_memory_tool_execution():
    """Test memory tool execution directly."""
    print("🧪 Testing Memory Tool Execution")
    print("=" * 50)
    
    try:
        # Load config and create memory manager
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        memory_manager = MemoryManager(config.get('memory', {}))
        print("✅ Memory manager created")
        
        # Create memory tools
        memory_tools = create_memory_tools(memory_manager)
        print(f"✅ Created {len(memory_tools)} memory tools")
        
        # Test each tool
        for tool in memory_tools:
            print(f"\n🔧 Testing tool: {tool.name}")
            
            if tool.name == "add_memory":
                # Test add_memory
                test_input = {
                    "content": "Test memory content for tool execution",
                    "agent_id": "test_agent",
                    "metadata": {"test": True, "source": "tool_test"}
                }
                
                print(f"   Input: {test_input}")
                
                try:
                    result = await tool.run(test_input)
                    print(f"   ✅ Result: {result}")
                    print(f"   ✅ Result type: {type(result)}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
            
            elif tool.name == "search_memory":
                # Test search_memory
                test_input = {
                    "query": "test",
                    "limit": 5
                }
                
                print(f"   Input: {test_input}")
                
                try:
                    result = await tool.run(test_input)
                    print(f"   ✅ Result: {result}")
                    print(f"   ✅ Result type: {type(result)}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the memory tool execution test."""
    print("🎯 Memory Tool Execution Test")
    print("=" * 60)
    
    success = await test_memory_tool_execution()
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    if success:
        print("✅ Memory tool execution test completed")
    else:
        print("❌ Memory tool execution test failed")

if __name__ == "__main__":
    asyncio.run(main()) 