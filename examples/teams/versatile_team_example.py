#!/usr/bin/env python3
"""
Versatile Team Example

This script demonstrates how to use the VersatileTeam class to handle different types of tasks
with its flexible and adaptable approach.
"""

import os
import sys
import asyncio
import argparse
from loguru import logger

# Add the project to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from roboco.teams.versatile import VersatileTeam
from roboco.core.models import Task


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


async def run_simple_task(workspace_dir: str, task_description: str):
    """Run a simple task using the VersatileTeam.
    
    Args:
        workspace_dir: Directory for workspace files
        task_description: Description of the task to execute
    """
    print_section(f"Running Task: {task_description[:40]}...")
    
    try:
        # Create the task
        task = Task(
            description=task_description,
            expected_outcome="Successfully complete the requested task"
        )
        
        # Create the team
        team = VersatileTeam(workspace_dir=workspace_dir)
        
        # Execute the task
        print("Starting task execution...")
        result = await team.execute_task(task)
        
        if result.get("status") == "completed":
            print("\n✅ Task completed successfully!")
            print(f"Results saved to: {result.get('results_path')}")
            print("\nTask Summary:")
            print("-------------")
            print(result.get("summary", "No summary available")[:500] + "...")
        else:
            print("\n❌ Task execution failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ Error running task: {str(e)}")


async def run_collaborative_task(workspace_dir: str, task_description: str):
    """Run a collaborative task with all team members.
    
    Args:
        workspace_dir: Directory for workspace files
        task_description: Description of the task to execute
    """
    print_section("Running Collaborative Task")
    
    try:
        # Create a task
        task = Task(
            description=task_description,
            expected_outcome="Complete the task with high quality results"
        )
        
        # Create the team
        team = VersatileTeam(workspace_dir=workspace_dir)
        
        # Execute the collaborative task
        print("Starting collaborative task session...")
        result = await team.run_chat(query=task_description)
        
        if result.get("status") == "completed":
            print("\n✅ Collaborative task completed successfully!")
            print(f"Results saved to: {result.get('results_path')}")
            
            # Show a snippet of the results
            if "response" in result:
                print("\nResult Preview:")
                print("--------------")
                response = result["response"]
                if isinstance(response, str):
                    print(response[:500] + "...")
                else:
                    print(str(response)[:500] + "...")
        else:
            print("\n❌ Collaborative task execution failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ Error running collaborative task: {str(e)}")


async def run_multiple_tasks(workspace_dir: str):
    """Run multiple tasks to demonstrate task sequence execution.
    
    Args:
        workspace_dir: Directory for workspace files
    """
    print_section("Running Multiple Tasks Sequence")
    
    try:
        # Create a list of tasks
        tasks = [
            Task(
                description="Research the key components of a successful blog post",
                expected_outcome="A list of key components and best practices"
            ),
            Task(
                description="Create an outline for a blog post about artificial intelligence trends",
                expected_outcome="A detailed outline with sections and key points"
            ),
            Task(
                description="Identify potential visual elements to enhance the blog post",
                expected_outcome="A list of image ideas, charts, and other visual elements"
            )
        ]
        
        # Create the team
        team = VersatileTeam(workspace_dir=workspace_dir)
        
        # Execute all tasks
        print("Starting execution of multiple tasks...")
        result = await team.execute_tasks(tasks)
        
        print("\n📊 Task Execution Summary:")
        print(f"  Total tasks: {len(tasks)}")
        print(f"  Completed: {result.get('completed', 0)}")
        print(f"  Failed: {result.get('failed', 0)}")
        
        # Print a summary of each task result
        print("\nIndividual Task Results:")
        print("----------------------")
        for i, task_result in enumerate(result.get("task_results", [])):
            status = "✅ Completed" if task_result.get("status") == "completed" else "❌ Failed"
            task_desc = task_result.get("task_description", f"Task {i+1}")
            print(f"{task_desc}: {status}")
            if task_result.get("status") == "completed":
                print(f"  Results: {task_result.get('results_path')}")
            else:
                print(f"  Error: {task_result.get('error', 'Unknown error')}")
            print()
    
    except Exception as e:
        print(f"\n❌ Error running multiple tasks: {str(e)}")


async def main():
    """Main function to parse arguments and run the example."""
    parser = argparse.ArgumentParser(description="Example script for using the VersatileTeam")
    parser.add_argument("--workspace", "-w", default="workspace",
                        help="Workspace directory (default: workspace)")
    parser.add_argument("--task", "-t", 
                        help="Task description for running a simple task")
    parser.add_argument("--collaborative", "-c", action="store_true",
                        help="Run as a collaborative task session")
    parser.add_argument("--multiple", "-m", action="store_true",
                        help="Run multiple tasks in sequence")
    
    args = parser.parse_args()
    
    # Ensure workspace directory exists
    os.makedirs(args.workspace, exist_ok=True)
    
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(os.path.join(args.workspace, "versatile_team_example.log"), level="DEBUG")
    
    print_section("Versatile Team Example")
    print(f"Workspace: {os.path.abspath(args.workspace)}")
    
    if args.collaborative and args.task:
        await run_collaborative_task(args.workspace, args.task)
    elif args.task:
        await run_simple_task(args.workspace, args.task)
    elif args.multiple:
        await run_multiple_tasks(args.workspace)
    else:
        # Default example task
        example_task = (
            "Create a concept for a mobile app that helps users track and reduce their carbon footprint. "
            "Include key features, target audience, and potential monetization strategies."
        )
        print("\nNo specific task option selected. Running default example task:")
        print(f"Task: {example_task}")
        await run_simple_task(args.workspace, example_task)


if __name__ == "__main__":
    asyncio.run(main()) 