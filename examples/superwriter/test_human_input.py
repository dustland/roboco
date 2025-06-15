#!/usr/bin/env python3
"""
Test script to verify human_input_mode is working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from agentx.core.team_manager import TeamManager
from agentx.event.bus import InMemoryEventBus

async def test_human_input_mode():
    """Test that human_input_mode NEVER works correctly."""
    
    # Set up environment
    os.environ["OPENAI_API_KEY"] = "test-key"  # Dummy key for testing
    
    # Create event bus
    event_bus = InMemoryEventBus()
    
    # Create team manager
    config_path = "config/default.yaml"
    team_manager = TeamManager(config_path, event_bus)
    
    print("🧪 Testing human_input_mode configuration...")
    
    # Check that agents have correct human_input_mode
    for agent_name, agent in team_manager.agents.items():
        print(f"Agent {agent_name}: human_input_mode = {getattr(agent, 'human_input_mode', 'NOT_SET')}")
    
    # Test with a simple task that should complete without human input
    simple_task = "Write a one-sentence summary of what AI is."
    
    print(f"\n🚀 Starting simple task: {simple_task}")
    print("This should complete without asking for human input...")
    
    try:
        result = await team_manager.run(
            task=simple_task,
            max_rounds=3,  # Keep it short
            human_input_mode="NEVER"  # Explicitly set to NEVER
        )
        
        print(f"\n✅ Task completed successfully!")
        print(f"Summary: {result.summary}")
        print(f"Success: {result.success}")
        print(f"Chat history length: {len(result.chat_history)}")
        
        # Print last few messages to see the conversation
        if result.chat_history:
            print("\n📝 Last few messages:")
            for i, msg in enumerate(result.chat_history[-3:]):
                print(f"  {i+1}. {msg.get('name', 'Unknown')}: {msg.get('content', '')[:100]}...")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_human_input_mode()) 