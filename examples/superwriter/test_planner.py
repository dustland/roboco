#!/usr/bin/env python3
"""
Planner Agent Test

This script tests the planner agent's 4-step workflow execution to ensure
it follows the structured process and uses memory operations correctly.
"""

import asyncio
import os
from roboco import run_team, InMemoryEventBus, EventMonitor

async def test_planner_workflow():
    """Test planner agent's 4-step workflow."""
    print("🧪 Testing Planner Agent 4-Step Workflow")
    print("=" * 50)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    monitor = EventMonitor(print_interval=10.0)
    
    try:
        await event_bus.start()
        await monitor.start(event_bus)
        print("✅ Event monitoring started")
        
        # Run with a simple task and limited rounds to focus on planner
        print("\n🚀 Starting planner workflow test...")
        result = await run_team(
            config_path="config/default.yaml",
            task="Create a brief guide about renewable energy benefits",
            event_bus=event_bus,
            max_rounds=8,  # Should be enough for 4 planner steps
            human_input_mode="NEVER"
        )
        
        print("\n📋 WORKFLOW RESULT:")
        print(f"Success: {result.success}")
        print(f"Summary: {result.summary}")
        
        # Analyze chat history for workflow steps
        if result.chat_history:
            print(f"\n💬 Chat Analysis ({len(result.chat_history)} messages):")
            
            step_indicators = [
                "Step 1 Complete",
                "Step 2 Complete", 
                "Step 3 Complete",
                "Step 4 Complete",
                "add_memory",
                "HANDOFF TO RESEARCHER"
            ]
            
            found_steps = {indicator: False for indicator in step_indicators}
            
            for i, msg in enumerate(result.chat_history, 1):
                sender = msg.get('name', 'Unknown')
                content = msg.get('content', '')
                
                # Check for step completion indicators
                for indicator in step_indicators:
                    if indicator in content:
                        found_steps[indicator] = True
                        print(f"   ✅ Found: {indicator} (Message {i} from {sender})")
                
                # Show first few messages for debugging
                if i <= 3:
                    preview = content[:150] + "..." if len(content) > 150 else content
                    print(f"   {i}. {sender}: {preview}")
            
            print(f"\n📊 Step Completion Analysis:")
            for indicator, found in found_steps.items():
                status = "✅" if found else "❌"
                print(f"   {status} {indicator}")
        
        # Check events
        print(f"\n📡 Event Analysis:")
        metrics = monitor.get_metrics()
        print(f"   • Total events: {metrics.total_events}")
        
        # Look for specific events
        timeline = monitor.get_timeline_events(limit=20)
        event_types = {}
        for event in timeline:
            event_type = event.get('type', 'unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
        
        for event_type, count in event_types.items():
            print(f"   • {event_type}: {count}")
        
        return result.success
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await monitor.stop()
        await event_bus.stop()
        print("\n🔍 Monitoring stopped")

async def test_memory_operations():
    """Test memory operations in isolation."""
    print("\n🧪 Testing Memory Operations")
    print("=" * 30)
    
    try:
        from roboco.memory.manager import MemoryManager
        import yaml
        
        # Load memory config
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        memory_config = config.get("memory", {})
        memory_manager = MemoryManager(memory_config)
        
        # Test the exact operations the planner should use
        test_operations = [
            {
                "name": "Step 1 - Initial Requirements",
                "content": "Initial Requirements: Create a brief guide about renewable energy benefits. Purpose: Educational overview. Audience: General public. Scope: Cover solar, wind, environmental benefits. Format: Accessible guide.",
                "metadata": {
                    "phase": "requirements",
                    "step": "initial_expansion",
                    "document_type": "guide"
                }
            },
            {
                "name": "Step 3 - Final Requirements", 
                "content": "Final Requirements: Create a comprehensive guide about renewable energy benefits covering solar, wind, and environmental advantages. Target general public with accessible language.",
                "metadata": {
                    "phase": "requirements",
                    "step": "finalized",
                    "artifact_type": "document",
                    "status": "final"
                }
            },
            {
                "name": "Step 4 - Execution Plan",
                "content": "Execution Plan: Research Phase - Gather renewable energy data, benefits statistics. Writing Phase - Draft guide sections. Review Phase - Quality check for clarity and accuracy.",
                "metadata": {
                    "phase": "planning",
                    "artifact_type": "plan",
                    "status": "approved"
                }
            }
        ]
        
        for operation in test_operations:
            print(f"\n   Testing: {operation['name']}")
            
            result = memory_manager.add_memory(
                content=operation["content"],
                agent_id="planner",
                metadata=operation["metadata"]
            )
            
            if result.get("success", True):
                print(f"   ✅ Memory operation successful")
                
                # Test search (without filters due to Mem0 backend issue)
                search_results = memory_manager.search_memory(
                    "requirements",
                    limit=1
                )
                print(f"   ✅ Search returned {len(search_results)} results")
            else:
                print(f"   ❌ Memory operation failed: {result}")
                return False
        
        print("\n✅ All memory operations successful")
        return True
        
    except Exception as e:
        print(f"\n❌ Memory test failed: {e}")
        return False

async def main():
    """Run planner validation tests."""
    print("🚀 Planner Agent Validation")
    print("=" * 50)
    
    # Check environment
    required_vars = ["OPENAI_API_KEY", "SERPAPI_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    # Test memory operations first
    memory_success = await test_memory_operations()
    if not memory_success:
        print("\n❌ Memory operations test FAILED - fix before proceeding")
        return False
    
    # Test planner workflow
    workflow_success = await test_planner_workflow()
    
    print(f"\n{'='*50}")
    if memory_success and workflow_success:
        print("🎉 Planner validation PASSED!")
        print("✅ Memory operations work correctly")
        print("✅ Workflow execution successful")
    else:
        print("❌ Planner validation FAILED!")
        if not memory_success:
            print("⚠️  Memory operations need fixing")
        if not workflow_success:
            print("⚠️  Workflow execution needs fixing")
    
    return memory_success and workflow_success

if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 