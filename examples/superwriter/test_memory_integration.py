#!/usr/bin/env python3
"""
Memory Integration Test

This script tests that memory tools are properly registered with agents
and can be called during conversations.
"""

import asyncio
import os
from roboco.core.team_manager import TeamManager

async def test_memory_tool_registration():
    """Test that memory tools are properly registered with agents."""
    print("🧪 Testing Memory Tool Registration")
    print("=" * 50)
    
    try:
        # Create team manager
        team = TeamManager(config_path="config/default.yaml")
        print("✅ TeamManager created")
        
        # Check if memory manager exists
        if hasattr(team, 'memory_manager') and team.memory_manager:
            print("✅ Memory manager initialized")
        else:
            print("❌ Memory manager not initialized")
            return False
        
        # Check agents and their tools
        for agent_name, agent in team.agents.items():
            print(f"\n🔍 Checking agent: {agent_name}")
            
            # Check if agent has LLM config
            if hasattr(agent, 'llm_config') and agent.llm_config:
                print(f"   ✅ Has LLM config")
                
                # Check registered tools
                if hasattr(agent, '_function_map'):
                    tools = list(agent._function_map.keys())
                    print(f"   📋 Registered tools: {tools}")
                    
                    # Check for memory tools
                    memory_tools = [tool for tool in tools if 'memory' in tool.lower()]
                    if memory_tools:
                        print(f"   ✅ Memory tools found: {memory_tools}")
                    else:
                        print(f"   ❌ No memory tools found")
                else:
                    print(f"   ❌ No function map found")
            else:
                print(f"   ⚠️  No LLM config")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_memory_operations():
    """Test direct memory operations."""
    print("\n🧪 Testing Direct Memory Operations")
    print("=" * 50)
    
    try:
        # Create team manager
        team = TeamManager(config_path="config/default.yaml")
        
        if not hasattr(team, 'memory_manager') or not team.memory_manager:
            print("❌ Memory manager not available")
            return False
        
        memory_manager = team.memory_manager
        
        # Test add memory
        print("1. Testing add_memory...")
        result = memory_manager.add_memory(
            content="Test memory for validation",
            agent_id="test_agent",
            metadata={"test": True, "purpose": "validation"}
        )
        print(f"   Result: {result}")
        
        # Test search memory
        print("2. Testing search_memory...")
        results = memory_manager.search_memory(
            "test memory",
            limit=5
        )
        print(f"   Found {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.get('content', 'No content')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_memory_tool_functions():
    """Test memory tools as callable functions."""
    print("\n🧪 Testing Memory Tool Functions")
    print("=" * 50)
    
    try:
        from roboco.builtin_tools.memory_tools import create_memory_tools
        from roboco.memory.manager import MemoryManager
        import yaml
        
        # Load memory config
        config = yaml.safe_load(open('config/default.yaml'))
        memory_manager = MemoryManager(config.get('memory', {}))
        
        # Create memory tools
        memory_tools = create_memory_tools(memory_manager)
        print(f"✅ Created {len(memory_tools)} memory tools")
        
        for tool in memory_tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Test add_memory tool
        add_tool = next(tool for tool in memory_tools if tool.name == "add_memory")
        result = add_tool(
            content="Test content from tool",
            agent_id="test_agent",
            metadata={"source": "tool_test"}
        )
        print(f"\n✅ add_memory tool result: {result}")
        
        # Test search_memory tool
        search_tool = next(tool for tool in memory_tools if tool.name == "search_memory")
        result = search_tool(
            query="test content",
            limit=3
        )
        print(f"\n✅ search_memory tool result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory tool function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all memory integration tests."""
    print("🎯 Memory Integration Test Suite")
    print("=" * 60)
    
    tests = [
        test_memory_tool_registration,
        test_direct_memory_operations,
        test_memory_tool_functions
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    if passed == total:
        print("🎉 All memory integration tests passed!")
    else:
        print("❌ Some tests failed - memory tools may not be working correctly")

if __name__ == "__main__":
    asyncio.run(main()) 