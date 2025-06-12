"""
Task CLI Functions

Provides command-line interface functions for task management that can be used
across different roboco applications and examples.
"""

import asyncio
from typing import Optional

from roboco import run_team, InMemoryEventBus, EventMonitor
from roboco.core.task_manager import TaskManager
from roboco.core.team_manager import TeamManager


async def list_tasks(workspace_path: str = "./workspace"):
    """List available task sessions with detailed information."""
    task_manager = TaskManager(workspace_path)
    
    print("📋 Task Sessions - Detailed View")
    print("=" * 80)
    
    # Get summary by status
    status_summary = task_manager.get_tasks_by_status_summary()
    
    # Show overview
    total_tasks = sum(info["count"] for info in status_summary.values())
    if total_tasks == 0:
        print("   No task sessions found.")
        return
    
    print(f"\n📊 Overview: {total_tasks} total tasks")
    print(f"   🟢 Active: {status_summary['active']['count']}")
    print(f"   ✅ Completed: {status_summary['completed']['count']}")
    print(f"   ⏸️  Paused: {status_summary['paused']['count']}")
    print(f"   ❌ Failed: {status_summary['failed']['count']}")
    
    # Show detailed listings for each status
    for status, emoji in [("active", "🟢"), ("paused", "⏸️"), ("completed", "✅"), ("failed", "❌")]:
        detailed_tasks = task_manager.list_tasks_detailed(status=status, limit=5, include_metadata=False)
        
        if detailed_tasks:
            print(f"\n{emoji} {status.upper()} TASKS:")
            print("-" * 60)
            
            for task in detailed_tasks:
                # Format the task description (truncate if too long)
                desc = task["description"]
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                
                print(f"   📝 {desc}")
                print(f"      ID: {task['task_id']} | Status: {task['status']}")
                print(f"      Progress: {task['progress']['current_round']}/{task['progress']['max_rounds']} rounds ({task['progress']['percentage']}%)")
                print(f"      Duration: {task['duration_human']} | Updated: {task['updated_at'][:19]}")
                print(f"      Resume: --resume {task['task_id']}")
                print()


async def list_tasks_compact(workspace_path: str = "./workspace"):
    """List tasks in a compact format for quick overview."""
    task_manager = TaskManager(workspace_path)
    
    print("📋 Quick Task Overview")
    print("=" * 60)
    
    # Get all tasks
    all_tasks = task_manager.list_tasks_detailed(limit=20, include_metadata=False)
    
    if not all_tasks:
        print("   No task sessions found.")
        return
    
    print(f"{'ID':<10} {'Status':<10} {'Progress':<12} {'Description':<30}")
    print("-" * 60)
    
    for task in all_tasks:
        desc = task["description"][:27] + "..." if len(task["description"]) > 30 else task["description"]
        progress = f"{task['progress']['current_round']}/{task['progress']['max_rounds']}"
        
        status_emoji = {
            "active": "🟢",
            "completed": "✅", 
            "paused": "⏸️",
            "failed": "❌"
        }.get(task["status"], "❓")
        
        print(f"{task['task_id']:<10} {status_emoji}{task['status']:<9} {progress:<12} {desc:<30}")


async def show_task_details(task_id: str, workspace_path: str = "./workspace"):
    """Show detailed information about a specific task."""
    task_manager = TaskManager(workspace_path)
    
    task_summary = task_manager.get_task_summary(task_id)
    if not task_summary:
        print(f"❌ Task {task_id} not found!")
        return
    
    print(f"📋 Task Details: {task_summary['task_id']}")
    print("=" * 80)
    
    print(f"📝 Description: {task_summary['description']}")
    print(f"🏷️  Status: {task_summary['status']}")
    print(f"🆔 Task ID: {task_summary['task_id']}")
    print(f"📅 Created: {task_summary['created_at']}")
    print(f"🔄 Updated: {task_summary['updated_at']}")
    print(f"⏱️  Duration: {task_summary['duration_human']}")
    print(f"📊 Progress: {task_summary['progress']['current_round']}/{task_summary['progress']['max_rounds']} rounds ({task_summary['progress']['percentage']}%)")
    print(f"⚙️  Config: {task_summary['config_path']}")
    
    if task_summary['metadata']:
        print(f"📋 Metadata:")
        for key, value in task_summary['metadata'].items():
            print(f"   • {key}: {value}")
    
    if task_summary['status'] in ['active', 'paused']:
        print(f"\n💡 Resume this task:")
        print(f"   --resume {task_summary['task_id']}")


async def resume_task(
    task_id: str, 
    max_rounds: int = 25,
    workspace_path: str = "./workspace"
):
    """Resume an existing task session."""
    task_manager = TaskManager(workspace_path)
    
    # Get task details
    task_session = task_manager.get_task(task_id)
    if not task_session:
        print(f"❌ Task {task_id} not found!")
        return None
    
    print(f"🔄 Resuming Task: {task_session.task_description}")
    print(f"📅 Originally created: {task_session.created_at}")
    print(f"🔢 Previous rounds: {task_session.current_round}")
    print("=" * 60)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    monitor = EventMonitor(print_interval=30.0)
    
    try:
        # Start monitoring
        await monitor.start(event_bus)
        print("🔍 Event monitoring started...")
        
        # Resume the task
        team_manager = TeamManager(
            config_path=task_session.config_path,
            event_bus=event_bus,
            task_id=task_id
        )
        
        result = await team_manager.run(
            task=task_session.task_description,
            max_rounds=max_rounds,
            human_input_mode="NEVER",  # Explicitly set to NEVER to prevent human input prompts
            continue_task=True
        )
        
        # Print results
        print("\n" + "="*60)
        print("📝 TASK RESUMED SUCCESSFULLY!")
        print("="*60)
        print(f"Summary: {result.summary}")
        print(f"Task ID: {result.task_id}")
        
        # Show final task status
        final_task = task_manager.get_task(task_id)
        if final_task:
            print(f"Final Status: {final_task.status}")
            print(f"Total Rounds: {final_task.current_round}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during task resumption: {e}")
        raise
    finally:
        await monitor.stop()
        print("🔍 Event monitoring stopped")


async def start_new_task(
    task_description: str, 
    config_path: str = "config/default.yaml",
    max_rounds: int = 50,
    workspace_path: str = "./workspace"
):
    """Start a new task session."""
    print(f"🚀 Starting New Task: {task_description}")
    print("=" * 60)
    
    # Set up event monitoring
    event_bus = InMemoryEventBus()
    monitor = EventMonitor(print_interval=30.0)
    
    try:
        # Start monitoring
        await monitor.start(event_bus)
        print("🔍 Event monitoring started...")
        
        # Run the team collaboration
        result = await run_team(
            config_path=config_path,
            task=task_description,
            event_bus=event_bus,
            max_rounds=max_rounds,
            human_input_mode="NEVER"  # Explicitly set to NEVER to prevent human input prompts
        )
        
        # Print results
        print("\n" + "="*60)
        print("📝 COLLABORATION COMPLETE!")
        print("="*60)
        print(f"Summary: {result.summary}")
        print(f"Task ID: {result.task_id}")
        
        # Show task session info
        if result.task_id:
            task_manager = TaskManager(workspace_path)
            task_session = task_manager.get_task(result.task_id)
            if task_session:
                print(f"Status: {task_session.status}")
                print(f"Rounds Used: {task_session.current_round}/{task_session.max_rounds}")
                print(f"\n💡 To resume this task later, use:")
                print(f"   --resume {result.task_id}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error during collaboration: {e}")
        raise
    finally:
        await monitor.stop()
        print("🔍 Event monitoring stopped")


async def find_similar_tasks(description: str, workspace_path: str = "./workspace"):
    """Find tasks that can be resumed based on description similarity."""
    task_manager = TaskManager(workspace_path)
    
    similar_tasks = task_manager.find_continuable_tasks(description)
    
    if similar_tasks:
        print(f"🔍 Found {len(similar_tasks)} similar tasks:")
        print("=" * 60)
        for task in similar_tasks:
            print(f"   • {task.task_id} - {task.task_description}")
            print(f"     Status: {task.status}, Updated: {task.updated_at}")
            print(f"     Resume with: --resume {task.task_id}")
            print()
    else:
        print("🔍 No similar tasks found for this description.")


def check_environment():
    """Check required environment variables."""
    import os
    
    required_vars = ["OPENAI_API_KEY", "SERPAPI_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these variables:")
        for var in missing_vars:
            print(f"   export {var}=your_key_here")
        print("\nThen try again.")
        return False
    return True


def show_default_help(workspace_path: str = "./workspace"):
    """Show default help when no arguments are provided."""
    task_manager = TaskManager(workspace_path)
    existing_tasks = task_manager.list_tasks(limit=1)
    
    if existing_tasks:
        print("📋 Existing tasks found. Here's a quick overview:")
        print()
        asyncio.run(list_tasks_compact(workspace_path))
        print("\n💡 Use --help for all options or --list for detailed view.")
    else:
        print("🚀 Roboco Multi-Agent Collaboration System")
        print("=" * 50)
        print("No existing tasks found.")
        print("\n💡 Start a new task:")
        print('   python main.py "Write a comprehensive guide on machine learning"')
        print("\n📋 Or see all options:")
        print("   python main.py --help") 