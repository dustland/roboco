#!/usr/bin/env python3
"""
Planner Memory Usage Test

This script tests the updated planner prompt to ensure it correctly uses
memory tools during the 4-step planning workflow.
"""

import asyncio
import os
from roboco import run_team, InMemoryEventBus
from roboco.memory.manager import MemoryManager
import yaml

async def test_planner_memory_usage():
    """Test that the planner agent uses memory tools correctly."""
    print("🧪 Testing Updated Planner Memory Usage")
    print("=" * 50)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    
    try:
        await event_bus.start()
        print("✅ Event bus started")
        
        # Create a simple task for the planner
        task = """
        Create a brief market analysis report for Tesla's 2024 performance.
        Focus on competitive advantages and market position.
        Keep it concise - 3-4 sections maximum.
        """
        
        print(f"🚀 Starting planner memory test...")
        print(f"Task: {task.strip()}")
        
        result = await run_team(
            config_path="config/default.yaml",
            task=task,
            max_rounds=10,  # Limited rounds to focus on planner
            event_bus=event_bus
        )
        
        print(f"\n✅ Test completed")
        print(f"📊 Result type: {type(result)}")
        
        # Check memory for planner artifacts
        print(f"\n🔍 Checking memory for planner artifacts...")
        
        # Load config and create memory manager
        with open("config/default.yaml", 'r') as f:
            config = yaml.safe_load(f)
        
        memory_manager = MemoryManager(config.get('memory', {}))
        
        # Search for planner artifacts
        searches = [
            ("requirements", "Requirements artifacts"),
            ("survey", "Survey artifacts"),
            ("execution_plan", "Execution plan artifacts"),
            ("planner", "All planner artifacts"),
        ]
        
        total_artifacts = 0
        for query, description in searches:
            try:
                results = memory_manager.search_memory(query, limit=10)
                count = len(results) if results else 0
                total_artifacts += count
                status = "✅" if count > 0 else "❌"
                print(f"{status} {description}: {count} found")
                
                # Show first result if found
                if results and count > 0:
                    first_result = results[0]
                    content_preview = first_result.get('content', '')[:100]
                    metadata = first_result.get('metadata', {})
                    print(f"   📝 Preview: {content_preview}...")
                    print(f"   🏷️  Metadata: {metadata}")
                    
            except Exception as e:
                print(f"❌ Error searching {description}: {e}")
        
        print(f"\n📊 Total planner artifacts found: {total_artifacts}")
        
        return result, total_artifacts
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None, 0
        
    finally:
        await event_bus.stop()
        print("✅ Event bus stopped")

async def main():
    """Run the planner memory usage test."""
    print("🎯 Planner Memory Usage Test")
    print("=" * 60)
    
    result, artifact_count = await test_planner_memory_usage()
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS")
    print("=" * 60)
    
    if result and artifact_count > 0:
        print("✅ SUCCESS: Planner is using memory tools correctly!")
        print(f"📊 Found {artifact_count} artifacts in memory")
    elif result and artifact_count == 0:
        print("⚠️  PARTIAL: Planner completed but no memory artifacts found")
        print("💡 Planner may not be following memory instructions")
    else:
        print("❌ FAILED: Planner test failed to complete")
    
    print("\nNext steps:")
    if artifact_count > 0:
        print("- ✅ Planner memory integration working")
        print("- 🚀 Ready to update researcher prompts")
    else:
        print("- 🔧 Need to further refine planner prompts")
        print("- 🔍 Check if memory instructions are clear enough")

if __name__ == "__main__":
    asyncio.run(main()) 