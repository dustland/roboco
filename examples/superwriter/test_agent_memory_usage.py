#!/usr/bin/env python3
"""
Agent Memory Usage Test

This script tests whether agents can actually use memory tools when explicitly
instructed to do so in their conversation.
"""

import asyncio
import os
from roboco import run_team, InMemoryEventBus

async def test_agent_memory_usage():
    """Test that agents can use memory tools when instructed."""
    print("🧪 Testing Agent Memory Tool Usage")
    print("=" * 50)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    
    try:
        await event_bus.start()
        print("✅ Event bus started")
        
        # Create a task that explicitly instructs agents to use memory
        task = """
        MEMORY TEST TASK:
        
        1. Planner: Use add_memory to store this requirement: "Create Tesla analysis with market position and competitive advantages"
        2. Researcher: Use search_memory to find the requirement, then use add_memory to store: "Research source: Tesla is leading EV market in 2024"
        3. Writer: Use search_memory to find both previous memories, then use add_memory to store: "Draft section: Tesla Market Leadership"
        4. Reviewer: Use search_memory to find all memories and provide feedback
        
        Each agent MUST use the memory tools (add_memory, search_memory) as instructed.
        """
        
        print(f"🚀 Starting memory usage test...")
        print(f"Task: {task[:100]}...")
        
        result = await run_team(
            config_path="config/default.yaml",
            task=task,
            max_rounds=15,  # Limited rounds to focus on memory usage
            event_bus=event_bus
        )
        
        print(f"\n✅ Test completed")
        print(f"📊 Result type: {type(result)}")
        print(f"📝 Result summary: {str(result)[:200]}...")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        await event_bus.stop()
        print("✅ Event bus stopped")

async def main():
    """Run the agent memory usage test."""
    print("🎯 Agent Memory Usage Test")
    print("=" * 60)
    
    result = await test_agent_memory_usage()
    
    print("\n" + "=" * 60)
    print("🏁 TEST COMPLETE")
    print("=" * 60)
    
    if result:
        print("✅ Agents were able to complete the memory test task")
    else:
        print("❌ Memory test failed - agents may not be using memory tools")

if __name__ == "__main__":
    asyncio.run(main()) 