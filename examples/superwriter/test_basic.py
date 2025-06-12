#!/usr/bin/env python3
"""
Basic SuperWriter Test

This script runs a minimal test of the SuperWriter system to validate
that the workflow can start and execute basic steps.
"""

import asyncio
import os
from roboco import run_team, InMemoryEventBus

async def test_basic_workflow():
    """Test basic workflow execution."""
    print("🧪 Testing Basic SuperWriter Workflow")
    print("=" * 50)
    
    # Set up minimal event monitoring
    event_bus = InMemoryEventBus()
    
    try:
        await event_bus.start()
        print("✅ Event bus started")
        
        # Run a very simple task with limited rounds
        print("\n🚀 Starting collaboration with simple task...")
        result = await run_team(
            config_path="config/default.yaml",
            task="Write a brief 2-paragraph summary about AI in healthcare",
            event_bus=event_bus,
            max_rounds=10,  # Limit rounds for testing
            human_input_mode="NEVER"  # Ensure no human input required
        )
        
        print("\n📋 COLLABORATION RESULT:")
        print(f"Success: {result.success}")
        print(f"Summary: {result.summary}")
        print(f"Participants: {', '.join(result.participants)}")
        
        if result.chat_history:
            print(f"\n💬 Chat History ({len(result.chat_history)} messages):")
            for i, msg in enumerate(result.chat_history[-3:], 1):  # Show last 3 messages
                sender = msg.get('name', 'Unknown')
                content = msg.get('content', '')[:200] + "..." if len(msg.get('content', '')) > 200 else msg.get('content', '')
                print(f"   {i}. {sender}: {content}")
        
        if result.error_message:
            print(f"\n⚠️  Error: {result.error_message}")
        
        return result.success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await event_bus.stop()
        print("\n🔍 Event bus stopped")

async def main():
    """Run the basic test."""
    # Check environment
    required_vars = ["OPENAI_API_KEY", "SERPAPI_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    success = await test_basic_workflow()
    
    if success:
        print("\n🎉 Basic test PASSED!")
        print("✅ SuperWriter system is working correctly")
    else:
        print("\n❌ Basic test FAILED!")
        print("⚠️  Check the errors above for issues to fix")
    
    return success

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 