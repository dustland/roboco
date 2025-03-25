"""
Example demonstrating the complete workflow from planning to execution.

This example:
1. Uses PlanningTeam to generate a project structure and todo.md
2. Uses ExecutionTeam to execute the tasks in the todo.md
"""
import asyncio
import os
import time
from typing import Dict, Any, List

from roboco.teams.planning import PlanningTeam
from roboco.teams.execution import ExecutionTeam


def print_section(title: str):
    """Print a section title."""
    print("\n" + "=" * 50)
    print(title)
    print("=" * 50)


def list_directory_contents(directory: str):
    """List the contents of a directory recursively."""
    print(f"Contents of {directory}:")
    for root, dirs, files in os.walk(directory):
        level = root.replace(directory, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            print(f"{sub_indent}{file}")


def print_execution_results(results: Dict[str, Any]):
    """Print execution results in a readable format."""
    print_section("Execution Results")
    
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    print(f"Overall success: {'✅ Success' if results.get('overall_success', False) else '❌ Failed'}")
    print(f"Total execution time: {results.get('execution_time', 0):.2f} seconds")
    print()
    
    for phase_result in results.get("phases", []):
        phase_name = phase_result.get("name", "Unknown")
        success = phase_result.get("success", False)
        skipped = phase_result.get("skipped", False)
        
        if skipped:
            print(f"⏭️  Phase: {phase_name} - Skipped (already completed)")
            continue
        
        print(f"{'✅' if success else '❌'} Phase: {phase_name}")
        
        for task_result in phase_result.get("tasks", []):
            task_title = task_result.get("title", "Unknown")
            task_status = task_result.get("status", "Unknown")
            task_skipped = task_result.get("skipped", False)
            
            if task_skipped:
                print(f"  ⏭️  {task_title} - Skipped (already completed)")
                continue
            
            status_icon = "✅" if task_status == "DONE" else "❌"
            print(f"  {status_icon} {task_title}")
            
            if "error" in task_result and task_result["error"]:
                print(f"     Error: {task_result['error']}")


async def plan_and_execute(query: str, workspace_dir: str, execute_phases: List[str] = None):
    """Plan and execute a project based on a query.
    
    Args:
        query: Query to generate a project for
        workspace_dir: Directory to create the project in
        execute_phases: Optional list of phases to execute (if None, execute all)
    """
    # Step 1: Create the Planning Team and generate project
    print_section("Planning Phase")
    print(f"Creating Planning Team for query: {query}")
    
    planning_team = PlanningTeam(workspace_dir=workspace_dir)
    
    # Generate the project structure and todo.md
    result = await planning_team.run_chat(query=query)
    
    if "error" in result:
        print(f"❌ Error in planning: {result['error']}")
        return
    
    print("✅ Planning completed successfully")
    
    # Step 2: Find the generated project directory
    project_dir = None
    for item in os.listdir(workspace_dir):
        item_path = os.path.join(workspace_dir, item)
        if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "todo.md")):
            project_dir = item_path
            break
    
    if not project_dir:
        print("❌ No project directory found with todo.md. Check the workspace directory manually.")
        return
    
    print(f"📁 Found project directory: {os.path.basename(project_dir)}")
    
    # Display the generated todo.md
    todo_path = os.path.join(project_dir, "todo.md")
    print_section("Generated Todo List")
    with open(todo_path, 'r') as file:
        print(file.read())
    
    # Step 3: Create the Execution Team and execute tasks
    print_section("Execution Phase")
    print("Creating Execution Team...")
    
    execution_team = ExecutionTeam(project_dir=project_dir)
    
    # Execute specific phases or all phases
    if execute_phases:
        for phase_name in execute_phases:
            print(f"Executing phase: {phase_name}")
            execution_result = await execution_team.execute_project(phase_filter=phase_name)
            print_execution_results(execution_result)
    else:
        print("Executing all phases...")
        execution_result = await execution_team.execute_project()
        print_execution_results(execution_result)
    
    # Display the final project structure
    print_section("Final Project Structure")
    list_directory_contents(project_dir)
    
    print_section("Test Complete")
    print("✅ The plan and execute test has completed.")


async def main():
    """Main function."""
    # Create workspace directory
    workspace_dir = os.path.join(os.path.dirname(__file__), "..", "..", "workspace")
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Define the test query
    query = "Build a beautiful todo app"
    
    # Run the plan and execute workflow
    await plan_and_execute(
        query=query,
        workspace_dir=workspace_dir,
        # Uncomment to execute specific phases only
        # execute_phases=["Research", "Design"]
    )


if __name__ == "__main__":
    asyncio.run(main())
