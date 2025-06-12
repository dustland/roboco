#!/usr/bin/env python3
"""
Memory-Driven Workflow Test

This script tests the updated SuperWriter system with memory-driven workflow
to ensure agents follow the 13-step process and use memory operations correctly.
"""

import asyncio
import os
from roboco import run_team, InMemoryEventBus, EventMonitor

async def test_memory_workflow():
    """Test the complete memory-driven workflow."""
    print("🧪 Testing Memory-Driven SuperWriter Workflow")
    print("=" * 60)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    monitor = EventMonitor(print_interval=15.0)
    
    try:
        await event_bus.start()
        await monitor.start(event_bus)
        print("✅ Event monitoring started")
        
        # Run with a focused task and reasonable round limit
        print("\n🚀 Starting memory-driven collaboration...")
        print("Task: Create a brief analysis of Tesla's market position")
        print("Expected workflow: Planner → Researcher → Reviewer → Writer → Final Review")
        print("-" * 60)
        
        result = await run_team(
            config_path="config/default.yaml",
            task="Create a brief analysis of Tesla's current market position and competitive advantages. Focus on 2024 data and keep it concise (3-4 sections max).",
            max_rounds=30,  # Reduced to focus on workflow completion
            event_bus=event_bus
        )
        
        print("\n" + "=" * 60)
        print("🎯 WORKFLOW TEST RESULTS")
        print("=" * 60)
        
        if result:
            print("✅ Collaboration completed successfully")
            print(f"📊 Final result type: {type(result)}")
            
            # Check if we have a final document
            if hasattr(result, 'summary') and result.summary:
                print("✅ Final document generated")
                print(f"📝 Document length: {len(result.summary)} characters")
            else:
                print("⚠️  No final document in result")
                
        else:
            print("❌ Collaboration failed or returned None")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            await monitor.stop()
            await event_bus.stop()
            print("\n✅ Event monitoring stopped")
        except:
            pass

async def analyze_memory_usage():
    """Analyze memory usage after the workflow."""
    print("\n🔍 MEMORY ANALYSIS")
    print("=" * 40)
    
    try:
        from roboco.memory.manager import MemoryManager
        import yaml
        
        # Load memory config
        config = yaml.safe_load(open('config/default.yaml'))
        memory_manager = MemoryManager(config.get('memory', {}))
        
        # Search for workflow artifacts
        workflow_searches = [
            ("requirements", "Requirements and planning"),
            ("execution_plan", "Execution plans"),
            ("research_sources", "Research sources"),
            ("section_draft", "Section drafts"),
            ("document_compiled", "Compiled documents"),
            ("reviewer_feedback", "Reviewer feedback")
        ]
        
        total_memories = 0
        for search_term, description in workflow_searches:
            try:
                # Search without agent_id filter to see all memories
                results = memory_manager.search_memory(search_term, limit=10)
                count = len(results) if results else 0
                total_memories += count
                status = "✅" if count > 0 else "❌"
                print(f"{status} {description}: {count} entries")
            except Exception as e:
                print(f"❌ {description}: Error searching - {e}")
        
        print(f"\n📊 Total workflow memories found: {total_memories}")
        
        if total_memories > 0:
            print("✅ Memory system is being used by agents")
        else:
            print("❌ No workflow memories found - agents may not be using memory")
            
    except Exception as e:
        print(f"❌ Memory analysis failed: {e}")

async def main():
    """Run the complete test suite."""
    print("🎯 SuperWriter Memory-Driven Workflow Validation")
    print("=" * 60)
    
    # Test 1: Memory-driven workflow
    await test_memory_workflow()
    
    # Test 2: Memory usage analysis
    await analyze_memory_usage()
    
    print("\n" + "=" * 60)
    print("🏁 VALIDATION COMPLETE")
    print("=" * 60)
    print("\nNext steps if issues found:")
    print("1. Check agent prompts for memory operation usage")
    print("2. Verify memory system configuration")
    print("3. Test individual agent memory operations")
    print("4. Review workflow state management")

if __name__ == "__main__":
    asyncio.run(main()) 