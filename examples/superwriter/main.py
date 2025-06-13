#!/usr/bin/env python3
"""
SuperWriter Multi-Agent Collaboration System

A comprehensive writing system with task session management and continuation capabilities.
Supports creating new tasks, continuing existing ones, and managing task sessions.
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import the new Task-centric API
import roboco


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables and try again:")
        for var in missing_vars:
            print(f"   export {var}='your_value_here'")
        return False
    
    return True


async def list_tasks_detailed():
    """List all tasks with detailed information."""
    tasks = roboco.list_tasks()
    
    if not tasks:
        print("📋 No tasks found.")
        return
    
    print(f"📋 Found {len(tasks)} tasks:")
    print()
    
    for task in tasks:
        info = task.get_info()
        print(f"🆔 Task ID: {info.task_id}")
        print(f"📝 Description: {info.description}")
        print(f"📊 Status: {info.status}")
        print(f"📅 Created: {info.created_at}")
        print(f"⚙️  Config: {info.config_path}")
        
        # Show memory info if available
        memory = task.get_memory()
        if memory:
            try:
                memories = memory.get_all(limit=1)
                print(f"🧠 Memories: {len(memories)} stored")
            except:
                print(f"🧠 Memories: Available")
        
        # Show chat history length
        chat = task.get_chat()
        history = chat.get_chat_history()
        print(f"💬 Chat history: {len(history)} messages")
        print("-" * 50)


async def list_tasks_compact():
    """List tasks in a compact table format."""
    tasks = roboco.list_tasks()
    
    if not tasks:
        print("📋 No tasks found.")
        return
    
    print(f"📋 {len(tasks)} tasks found:")
    print()
    print(f"{'ID':<10} {'Status':<12} {'Description':<50} {'Created':<20}")
    print("-" * 92)
    
    for task in tasks:
        info = task.get_info()
        desc = info.description[:47] + "..." if len(info.description) > 50 else info.description
        created = info.created_at.strftime("%Y-%m-%d %H:%M") if info.created_at else "Unknown"
        print(f"{info.task_id:<10} {info.status:<12} {desc:<50} {created:<20}")


async def show_task_details(task_id):
    """Show detailed information about a specific task."""
    try:
        task = roboco.get_task(task_id)
        if not task:
            print(f"❌ Task '{task_id}' not found.")
            return
        
        info = task.get_info()
        print(f"🆔 Task Details: {info.task_id}")
        print("=" * 50)
        print(f"📝 Description: {info.description}")
        print(f"📊 Status: {info.status}")
        print(f"📅 Created: {info.created_at}")
        print(f"⚙️  Config: {info.config_path}")
        
        # Show memory information
        memory = task.get_memory()
        if memory:
            try:
                all_memories = memory.get_all(limit=10)
                print(f"\n🧠 Memory ({len(all_memories)} entries):")
                for i, mem in enumerate(all_memories[:5], 1):
                    content = mem.get('content', '')[:100]
                    agent = mem.get('agent_id', 'unknown')
                    print(f"   {i}. [{agent}] {content}...")
                if len(all_memories) > 5:
                    print(f"   ... and {len(all_memories) - 5} more")
            except Exception as e:
                print(f"🧠 Memory: Available (error accessing: {e})")
        else:
            print(f"🧠 Memory: Not available")
        
        # Show chat history
        chat = task.get_chat()
        history = chat.get_chat_history()
        print(f"\n💬 Chat History ({len(history)} messages):")
        for i, msg in enumerate(history[-5:], 1):  # Show last 5 messages
            sender = msg.get('name', msg.get('sender', 'unknown'))
            content = msg.get('content', '')[:100]
            print(f"   {i}. [{sender}] {content}...")
        if len(history) > 5:
            print(f"   ... and {len(history) - 5} more messages")
        
    except Exception as e:
        print(f"❌ Error showing task details: {e}")


async def resume_task_by_id(task_id, max_rounds=25):
    """Resume an existing task by ID."""
    try:
        task = roboco.get_task(task_id)
        if not task:
            print(f"❌ Task '{task_id}' not found.")
            return
        
        info = task.get_info()
        print(f"🔄 Resuming task: {info.task_id}")
        print(f"📝 Description: {info.description}")
        print(f"📊 Current status: {info.status}")
        print(f"🚀 Starting continuation with max {max_rounds} rounds...\n")
        
        # Continue the task
        continuation_prompt = f"""
        Continue working on this task. Review the previous work and continue from where we left off.
        
        Original task: {info.description}
        
        Please continue the collaboration and complete any remaining work.
        """
        
        result = await task.start(continuation_prompt)
        
        if result and result.success:
            print(f"\n✅ Task continuation completed successfully!")
            print(f"📊 Total conversation rounds: {len(result.conversation_history)}")
            print(f"📝 Summary: {result.summary}")
        else:
            print(f"\n❌ Task continuation failed: {result.summary if result else 'Unknown error'}")
            
    except Exception as e:
        print(f"❌ Error resuming task: {e}")
        import traceback
        traceback.print_exc()


async def start_new_task(description, config_path, max_rounds=50):
    """Start a new task with the given description."""
    try:
        print(f"🚀 Starting new task...")
        print(f"📝 Description: {description}")
        print(f"⚙️  Config: {config_path}")
        print(f"🔄 Max rounds: {max_rounds}\n")
        
        # Create and start the task
        task = roboco.create_task(
            config_path=config_path,
            description=description
        )
        
        print(f"✅ Created task: {task.task_id}")
        
        result = await task.start(description)
        
        if result and result.success:
            print(f"\n✅ Task completed successfully!")
            print(f"🆔 Task ID: {task.task_id}")
            print(f"📊 Total conversation rounds: {len(result.conversation_history)}")
            print(f"📝 Summary: {result.summary}")
            
            # Show memory info
            memory = task.get_memory()
            if memory:
                try:
                    memories = memory.get_all(limit=1)
                    print(f"🧠 Memories stored: {len(memories)}")
                except:
                    print(f"🧠 Memory system active")
            
        else:
            print(f"\n❌ Task failed: {result.summary if result else 'Unknown error'}")
            print(f"🆔 Task ID: {task.task_id} (saved for potential resumption)")
            
    except Exception as e:
        print(f"❌ Error starting task: {e}")
        import traceback
        traceback.print_exc()


async def find_similar_tasks(description):
    """Find tasks with similar descriptions."""
    tasks = roboco.list_tasks()
    
    if not tasks:
        print("📋 No tasks found to search.")
        return
    
    # Simple keyword matching (could be enhanced with semantic search)
    keywords = description.lower().split()
    matches = []
    
    for task in tasks:
        info = task.get_info()
        task_desc = info.description.lower()
        
        # Count keyword matches
        match_count = sum(1 for keyword in keywords if keyword in task_desc)
        if match_count > 0:
            matches.append((task, match_count))
    
    # Sort by match count
    matches.sort(key=lambda x: x[1], reverse=True)
    
    if not matches:
        print(f"🔍 No tasks found matching '{description}'")
        return
    
    print(f"🔍 Found {len(matches)} similar tasks:")
    print()
    
    for task, match_count in matches[:10]:  # Show top 10 matches
        info = task.get_info()
        desc = info.description[:60] + "..." if len(info.description) > 63 else info.description
        print(f"🆔 {info.task_id} ({match_count} matches)")
        print(f"   📝 {desc}")
        print(f"   📊 Status: {info.status}")
        print()


async def show_default_help():
    """Show default help with existing tasks or usage instructions."""
    tasks = roboco.list_tasks()
    
    if tasks:
        print("📋 Recent tasks:")
        await list_tasks_compact()
        print("\n💡 Use --resume <TASK_ID> to continue a task")
        print("💡 Use --details <TASK_ID> to see task details")
    else:
        print("🤖 SuperWriter Multi-Agent Collaboration System")
        print("\n📝 Start a new writing task:")
        print("   python main.py 'Write a guide on sustainable energy'")
        print("\n📋 Manage tasks:")
        print("   python main.py --list          # List all tasks")
        print("   python main.py --resume <ID>   # Resume a task")
        print("   python main.py --details <ID>  # Show task details")
        print("\n🔍 Find tasks:")
        print("   python main.py --find 'energy' # Find similar tasks")
        print("\n❓ For more help:")
        print("   python main.py --help")


async def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="SuperWriter Multi-Agent Collaboration System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Write a guide on AI ethics"           # Start new task
  python main.py --resume f3THoi5x                      # Resume task by ID
  python main.py --list                                 # List all tasks (detailed)
  python main.py --list-compact                         # List tasks (compact)
  python main.py --details f3THoi5x                     # Show task details
  python main.py --find "AI ethics"                     # Find similar tasks
        """
    )
    
    # Task operations
    parser.add_argument("task", nargs="?", help="Task description for new collaboration")
    parser.add_argument("--resume", type=str, metavar="TASK_ID", help="Resume existing task by ID")
    
    # Listing operations
    parser.add_argument("--list", action="store_true", help="List all task sessions (detailed view)")
    parser.add_argument("--list-compact", action="store_true", help="List tasks in compact table format")
    parser.add_argument("--details", type=str, metavar="TASK_ID", help="Show detailed information about a specific task")
    parser.add_argument("--find", type=str, metavar="DESCRIPTION", help="Find similar tasks by description")
    
    # Configuration
    parser.add_argument("--max-rounds", type=int, default=50, help="Maximum rounds for collaboration (default: 50)")
    
    args = parser.parse_args()
    
    # Check environment variables
    if not check_environment():
        return
    
    # Handle different operations
    if args.list:
        await list_tasks_detailed()
    elif args.list_compact:
        await list_tasks_compact()
    elif args.details:
        await show_task_details(args.details)
    elif args.resume:
        await resume_task_by_id(args.resume, args.max_rounds)
    elif args.find:
        await find_similar_tasks(args.find)
    elif args.task:
        await start_new_task(args.task, "config/default.yaml", args.max_rounds)
    else:
        # Default behavior - show existing tasks or help
        await show_default_help()


if __name__ == "__main__":
    asyncio.run(main()) 