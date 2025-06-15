#!/usr/bin/env python3
"""
Debug script to test task persistence and identify the issue.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from agentx.core.task_manager import TaskManager
from agentx.core.team_manager import TeamManager
from agentx.event.bus import InMemoryEventBus

async def test_task_persistence():
    """Test task persistence to identify the issue."""
    
    print("🧪 Testing Task Persistence...")
    
    # Set up environment
    os.environ["OPENAI_API_KEY"] = "test-key"  # Dummy key for testing
    
    # Test 1: Direct TaskManager test
    print("\n1️⃣ Testing TaskManager directly...")
    workspace_path = "workspace"
    task_manager = TaskManager(workspace_path)
    
    print(f"🔍 TaskManager workspace: {task_manager.workspace_path}")
    print(f"🔍 TaskManager sessions file: {task_manager.sessions_file}")
    
    # Create a test task
    task_id = task_manager.create_task(
        task_description="Test task persistence",
        config_path="config/default.yaml",
        max_rounds=10,
        metadata={"test": True}
    )
    
    print(f"✅ Created task: {task_id}")
    
    # Verify it was saved
    saved_task = task_manager.get_task(task_id)
    if saved_task:
        print(f"✅ Task saved successfully: {saved_task.task_id}")
    else:
        print(f"❌ Task NOT saved!")
        return
    
    # Test 2: TeamManager with exception simulation
    print("\n2️⃣ Testing TeamManager with simulated exception...")
    
    event_bus = InMemoryEventBus()
    await event_bus.start()
    
    try:
        team_manager = TeamManager(
            config_path="config/default.yaml",
            event_bus=event_bus
        )
        
        print(f"🔍 TeamManager config_path: {team_manager.config_path}")
        print(f"🔍 TeamManager task_manager workspace: {team_manager.task_manager.workspace_path}")
        print(f"🔍 TeamManager task_manager sessions file: {team_manager.task_manager.sessions_file}")
        
        # This should create a task but then fail due to invalid API key
        result = await team_manager.run(
            task="Test task that will fail",
            max_rounds=5,
            human_input_mode="NEVER"
        )
        
        print(f"Result: {result}")
        print(f"Task ID: {result.task_id}")
        
        # Check if task was saved despite the failure
        if result.task_id:
            # Check with the SAME task manager instance
            failed_task = team_manager.task_manager.get_task(result.task_id)
            if failed_task:
                print(f"✅ Failed task found in TeamManager's task_manager: {failed_task.task_id}, Status: {failed_task.status}")
            else:
                print(f"❌ Failed task NOT found in TeamManager's task_manager!")
            
            # Check with a NEW task manager instance
            new_task_manager = TaskManager(workspace_path)
            failed_task_new = new_task_manager.get_task(result.task_id)
            if failed_task_new:
                print(f"✅ Failed task found in NEW task_manager: {failed_task_new.task_id}, Status: {failed_task_new.status}")
            else:
                print(f"❌ Failed task NOT found in NEW task_manager!")
        
    except Exception as e:
        print(f"Exception during team manager test: {e}")
    
    # Test 3: List all tasks
    print("\n3️⃣ Listing all tasks...")
    all_tasks = task_manager.list_tasks(limit=20)
    for task in all_tasks:
        print(f"   • {task.task_id}: {task.task_description[:50]}... (Status: {task.status})")
    
    await event_bus.stop()

if __name__ == "__main__":
    asyncio.run(test_task_persistence()) 