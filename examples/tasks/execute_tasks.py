#!/usr/bin/env python
"""
Task Execution Example

This example demonstrates how to use the ProjectExecutor to execute tasks defined in a tasks.md file.
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from loguru import logger

# Add project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.core.project_executor import ProjectExecutor

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

def print_section(title):
    """Print a section heading."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def print_results(results):
    """Print execution results in a structured way."""
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"Overall Status: {'✅ Success' if results['overall_status'] == 'success' else '⚠️ Partial Failure'}")
    
    for phase_name, phase_result in results["phases"].items():
        print(f"\nPhase: {phase_name} - {'✅ Success' if phase_result['status'] == 'success' else '⚠️ Partial Failure'}")
        
        for task_name, task_result in phase_result["tasks"].items():
            status_icon = "✅" if task_result["status"] == "completed" else "⏭️" if task_result["status"] == "already_completed" else "❌"
            print(f"  {status_icon} Task: {task_name} - {task_result['status']}")
            
            if task_result["status"] == "failed" and "error" in task_result:
                print(f"     Error: {task_result['error']}")

async def execute_single_task(project_dir, task_title):
    """Execute a single task by title."""
    print_section(f"Executing Single Task: {task_title}")
    
    executor = ProjectExecutor(project_dir)
    results = await executor.execute_task(task_title)
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"Task: {results['task']} in Phase: {results['phase']}")
    print(f"Status: {'✅ Success' if results['result']['status'] == 'success' else '⚠️ Partial Failure'}")
    
    # Print detailed task results
    task_results = next(iter(results['result']['tasks'].values()))
    if task_results['status'] == 'completed':
        print(f"✅ Task completed successfully")
    elif task_results['status'] == 'already_completed':
        print(f"⏭️ Task was already completed")
    else:
        print(f"❌ Task failed: {task_results.get('error', 'Unknown error')}")

async def execute_phase(project_dir, phase_name):
    """Execute all tasks in a specific phase."""
    print_section(f"Executing Phase: {phase_name}")
    
    executor = ProjectExecutor(project_dir)
    results = await executor.execute_project(phase_filter=phase_name)
    
    print_results(results)

async def execute_all_phases(project_dir):
    """Execute all phases in the project."""
    print_section("Executing All Phases")
    
    executor = ProjectExecutor(project_dir)
    results = await executor.execute_project()
    
    print_results(results)

async def main():
    """Run the task execution example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Execute tasks from a tasks.md file")
    parser.add_argument("--project", "-p", type=str, required=True, help="Path to the project directory containing tasks.md")
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--task", "-t", type=str, help="Execute a specific task by title")
    group.add_argument("--phase", "-ph", type=str, help="Execute all tasks in a specific phase")
    group.add_argument("--all", "-a", action="store_true", help="Execute all phases")
    
    args = parser.parse_args()
    
    # Ensure project directory exists
    project_dir = args.project
    if not os.path.exists(project_dir):
        print(f"Error: Project directory does not exist: {project_dir}")
        return
    
    if not os.path.exists(os.path.join(project_dir, "tasks.md")):
        print(f"Error: tasks.md not found in project directory: {project_dir}")
        return
    
    # Execute tasks based on command line arguments
    if args.task:
        await execute_single_task(project_dir, args.task)
    elif args.phase:
        await execute_phase(project_dir, args.phase)
    elif args.all:
        await execute_all_phases(project_dir)
    else:
        print("Please specify one of: --task, --phase, or --all")
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main()) 