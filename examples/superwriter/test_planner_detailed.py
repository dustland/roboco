#!/usr/bin/env python3
"""
Detailed Planner Test

This script captures the actual conversation to see what the planner agent
is doing and whether it's following the memory instructions.
"""

import asyncio
import os
from roboco.core.team_manager import TeamManager
from roboco import InMemoryEventBus

async def test_planner_detailed():
    """Test planner with detailed conversation capture."""
    print("🧪 Detailed Planner Test")
    print("=" * 50)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    
    try:
        await event_bus.start()
        print("✅ Event bus started")
        
        # Create team manager directly for more control
        team = TeamManager(config_path="config/default.yaml")
        print("✅ Team manager created")
        
        # Check if planner has memory tools
        planner_agent = team.agents.get('planner')  # Use dictionary access
        
        if planner_agent:
            print(f"✅ Found planner agent")
            # Check tools
            if hasattr(planner_agent, '_function_map'):
                tools = list(planner_agent._function_map.keys()) if planner_agent._function_map else []
                print(f"📋 Planner tools: {tools}")
                
                # Check for memory tools specifically
                memory_tools = [tool for tool in tools if 'memory' in tool.lower()]
                if memory_tools:
                    print(f"✅ Memory tools found: {memory_tools}")
                else:
                    print(f"❌ No memory tools found")
            else:
                print("❌ Planner has no _function_map attribute")
        else:
            print("❌ Planner agent not found")
            print(f"Available agents: {list(team.agents.keys())}")
        
        # Create a simple task
        task = "Create a brief analysis of Tesla's market position. Focus on competitive advantages."
        
        print(f"\n🚀 Starting detailed test...")
        print(f"Task: {task}")
        
        # Run with very limited rounds to see initial behavior
        result = await team.run(
            task=task,
            max_rounds=8  # Increased to see more conversation
        )
        
        print(f"\n✅ Test completed")
        print(f"📊 Result: {result}")
        print(f"📊 Success: {result.success}")
        print(f"📊 Summary: {result.summary}")
        
        # Check conversation history
        if result.chat_history:
            print(f"\n💬 Conversation History ({len(result.chat_history)} messages):")
            for i, msg in enumerate(result.chat_history):
                # Handle different message formats
                if hasattr(msg, 'name'):
                    sender = msg.name
                    content = getattr(msg, 'content', str(msg))
                elif isinstance(msg, dict):
                    sender = msg.get('name', msg.get('role', 'unknown'))
                    content = msg.get('content', str(msg))
                else:
                    sender = 'unknown'
                    content = str(msg)
                
                # Truncate long content
                content_preview = content[:300] + "..." if len(content) > 300 else content
                print(f"  {i+1}. {sender}: {content_preview}")
                
                # Look for tool calls
                if 'tool call' in content.lower() or 'function call' in content.lower():
                    print(f"      🔧 TOOL CALL DETECTED!")
        else:
            print(f"\n❌ No conversation history available")
        
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
    """Run the detailed planner test."""
    print("🎯 Detailed Planner Analysis")
    print("=" * 60)
    
    result = await test_planner_detailed()
    
    print("\n" + "=" * 60)
    print("🏁 ANALYSIS COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 