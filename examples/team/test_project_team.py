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

from roboco.teams.project_team import ProjectTeam
from roboco.core.config import load_config, get_llm_config
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
    
    # Create workspace directory
    workspace_dir = "workspace/test_project"
    os.makedirs(workspace_dir, exist_ok=True)
    
    # Load config for LLM settings
    config = load_config()
    llm_config = get_llm_config(config)
    
    # Create the project team
    print("Creating Project Team...")
    project_team = ProjectTeam(
        llm_config=llm_config,
        workspace_dir=workspace_dir
    )
    
    # Define the test query
    query = "Create a simple todo app with React frontend and FastAPI backend"
    teams = ["frontend", "backend"]
    
    print(f"\nTest Query: {query}")
    print(f"Teams: {teams}")
    
    # Run the chat
    print("\nRunning chat with project builder...")
    result = await project_team.run_chat(query=query, teams=teams)
    
    # Print the response
    print_section("Project Builder Response")
    print(result["response"])
    
    # Check if project was created
    print_section("Project Structure")
    list_directory_contents(workspace_dir)
    
    print_section("Test Complete")
    print("✅ The ProjectTeam test has completed.")
    print("Check the output above to verify if the project was created successfully.")

if __name__ == "__main__":
    asyncio.run(main())
