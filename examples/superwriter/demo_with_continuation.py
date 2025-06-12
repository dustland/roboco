#!/usr/bin/env python3
"""
SuperWriter Demo with Task Continuation Support

This demo showcases task session management and continuation capabilities.
You can start a task, let it run to completion or interruption, and then
continue from where it left off using the stored memory and session state.

Features:
- Task session creation and tracking
- Memory isolation per task
- Continuation from previous sessions
- Task listing and management
"""

import asyncio
import os
import argparse
from roboco import run_team, InMemoryEventBus, EventMonitor
from roboco.core.task_manager import TaskManager

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
                print(f"      Continue: python demo_with_continuation.py --continue-task {task['task_id']}")
                print()

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
        print(f"\n💡 Continue this task:")
        print(f"   python demo_with_continuation.py --continue-task {task_summary['task_id']}")

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

async def continue_task(task_id: str, max_rounds: int = 25):
    """Continue an existing task session."""
    workspace_path = "./workspace"
    task_manager = TaskManager(workspace_path)
    
    # Get task details
    task_session = task_manager.get_task(task_id)
    if not task_session:
        print(f"❌ Task {task_id} not found!")
        return
    
    print(f"🔄 Continuing Task: {task_session.task_description}")
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
        
        # Continue the task
        from roboco.core.team_manager import TeamManager
        team_manager = TeamManager(
            config_path=task_session.config_path,
            event_bus=event_bus,
            task_id=task_id
        )
        
        result = await team_manager.run(
            task=task_session.task_description,
            max_rounds=max_rounds,
            continue_task=True
        )
        
        # Print results
        print("\n" + "="*60)
        print("📝 CONTINUATION COMPLETE!")
        print("="*60)
        print(f"Summary: {result.summary}")
        print(f"Task ID: {result.task_id}")
        
        # Show final task status
        final_task = task_manager.get_task(task_id)
        if final_task:
            print(f"Final Status: {final_task.status}")
            print(f"Total Rounds: {final_task.current_round}")
        
    except Exception as e:
        print(f"❌ Error during continuation: {e}")
        raise
    finally:
        await monitor.stop()
        print("🔍 Event monitoring stopped")

async def start_new_task(task_description: str, max_rounds: int = 50):
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
            config_path="config/default.yaml",
            task=task_description,
            event_bus=event_bus,
            max_rounds=max_rounds
        )
        
        # Print results
        print("\n" + "="*60)
        print("📝 COLLABORATION COMPLETE!")
        print("="*60)
        print(f"Summary: {result.summary}")
        print(f"Task ID: {result.task_id}")
        
        # Show task session info
        if result.task_id:
            workspace_path = "./workspace"
            task_manager = TaskManager(workspace_path)
            task_session = task_manager.get_task(result.task_id)
            if task_session:
                print(f"Status: {task_session.status}")
                print(f"Rounds Used: {task_session.current_round}/{task_session.max_rounds}")
                print(f"\n💡 To continue this task later, use:")
                print(f"   python demo_with_continuation.py --continue-task {result.task_id}")
        
    except Exception as e:
        print(f"❌ Error during collaboration: {e}")
        raise
    finally:
        await monitor.stop()
        print("🔍 Event monitoring stopped")

async def find_continuable_tasks(description: str):
    """Find tasks that can be continued based on description similarity."""
    workspace_path = "./workspace"
    task_manager = TaskManager(workspace_path)
    
    continuable = task_manager.find_continuable_tasks(description)
    
    if continuable:
        print(f"🔍 Found {len(continuable)} potentially continuable tasks:")
        print("=" * 60)
        for task in continuable:
            print(f"   • {task.task_id[:8]}... - {task.task_description}")
            print(f"     Status: {task.status}, Updated: {task.updated_at}")
            print(f"     Continue with: python demo_with_continuation.py --continue-task {task.task_id}")
            print()
    else:
        print("🔍 No continuable tasks found for this description.")

async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(description="SuperWriter with Task Continuation")
    parser.add_argument("--task", type=str, help="Task description for new collaboration")
    parser.add_argument("--continue-task", type=str, help="Continue existing task by ID")
    parser.add_argument("--list", action="store_true", help="List available task sessions (detailed)")
    parser.add_argument("--list-compact", action="store_true", help="List tasks in compact format")
    parser.add_argument("--details", type=str, help="Show detailed information about a specific task")
    parser.add_argument("--find", type=str, help="Find continuable tasks by description")
    parser.add_argument("--max-rounds", type=int, default=50, help="Maximum rounds for collaboration")
    
    args = parser.parse_args()
    
    # Check required environment variables
    required_vars = ["OPENAI_API_KEY", "SERPAPI_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables and try again.")
        return
    
    if args.list:
        await list_tasks()
    elif args.list_compact:
        await list_tasks_compact()
    elif args.details:
        await show_task_details(args.details)
    elif args.continue_task:
        await continue_task(args.continue_task, args.max_rounds)
    elif args.find:
        await find_continuable_tasks(args.find)
    elif args.task:
        await start_new_task(args.task, args.max_rounds)
    else:
        # Default behavior - show compact list if tasks exist, otherwise start new task
        task_manager = TaskManager("./workspace")
        existing_tasks = task_manager.list_tasks(limit=1)
        
        if existing_tasks:
            print("📋 Existing tasks found. Use --help for options or --list for detailed view.")
            await list_tasks_compact()
        else:
            default_task = "Write a comprehensive article about the future of AI in healthcare"
            print("No tasks found. Starting default task...")
            await start_new_task(default_task, args.max_rounds)

if __name__ == "__main__":
    asyncio.run(main()) 