#!/usr/bin/env python
"""
Test Project Team

This script tests the ProjectTeam implementation to verify it can:
1. Complete a conversation between the human proxy and project builder
2. Successfully create a project folder with the correct structure
3. Generate appropriate project metadata

Usage:
    python test_project_team.py
"""

import asyncio
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add project root to Python path (if running directly)
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from roboco.teams.planning import PlanningTeam
from loguru import logger

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")

def print_section(title):
    """Print a section heading."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2, default=str))

def list_directory_contents(path, indent=0):
    """List the contents of a directory recursively."""
    if not os.path.exists(path):
        print(f"Path does not exist: {path}")
        return
        
    print(f"{'  ' * indent}📁 {os.path.basename(path)}/")
    
    for item in sorted(os.listdir(path)):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path):
            list_directory_contents(item_path, indent + 1)
        else:
            print(f"{'  ' * (indent + 1)}📄 {item}")

async def main():
    """Run the Project Team test."""
    print_section("Project Team Test")
    
    # Set base workspace directory
    workspace_dir = "workspace"
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Create the project team
    print("Creating Project Team...")
    planning_team = PlanningTeam(
        workspace_dir=workspace_dir
    )
    
    # Define the test query
    query = "Create a simple todo app with popular tech stacks"
    # Run the chat
    print(f"\nRunning chat with project builder... query: {query}")

    result = await planning_team.run_chat(query=query)
    
    # Print the response
    print_section("Project Builder Response")
    print(result["response"])
    
    # Print the chat history
    print_section("Chat History")
    for msg in result.get("chat_history", []):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        print(f"{role.upper()}: {content[:100]}..." if len(content) > 100 else f"{role.upper()}: {content}")
    
    # List the created project structure
    print_section("Project Structure")
    for item in os.listdir(workspace_dir):
        item_path = os.path.join(workspace_dir, item)
        if os.path.isdir(item_path) and item.startswith("todo"):  # Look for todo app directory
            print(f"Found project directory: {item}")
            list_directory_contents(item_path)
            break
    else:
        print("No todo app project directory found. Check the workspace directory manually.")
    
    print_section("Test Complete")
    print("✅ The ProjectTeam test has completed.")
    print("Check the output above to verify if the project was created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
