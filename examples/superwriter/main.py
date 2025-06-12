#!/usr/bin/env python3
"""
SuperWriter Multi-Agent Collaboration System

A comprehensive writing system with task session management and continuation capabilities.
Supports creating new tasks, continuing existing ones, and managing task sessions.
"""

import asyncio
import argparse
import os

from roboco import (
    list_tasks, list_tasks_compact, show_task_details, resume_task,
    start_new_task, find_similar_tasks, check_environment, show_default_help
)


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
        await list_tasks()
    elif args.list_compact:
        await list_tasks_compact()
    elif args.details:
        await show_task_details(args.details)
    elif args.resume:
        await resume_task(args.resume, args.max_rounds)
    elif args.find:
        await find_similar_tasks(args.find)
    elif args.task:
        await start_new_task(args.task, "config/default.yaml", args.max_rounds)
    else:
        # Default behavior - show existing tasks or help
        await show_default_help()


if __name__ == "__main__":
    asyncio.run(main()) 