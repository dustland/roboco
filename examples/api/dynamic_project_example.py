#!/usr/bin/env python
"""
Dynamic Project Creation Example

This script demonstrates how to use the RoboCo API to create a project dynamically from a query.
It shows the process of:
1. Creating a project from a natural language query
2. Retrieving the generated project structure
3. Exploring the auto-generated sprint and tasks
4. Creating a job associated with the project
"""

import os
import json
import time
from datetime import datetime
import requests

# API Configuration
API_BASE_URL = "http://localhost:8000"  # Update if your server uses a different URL

def print_section(title):
    """Print a formatted section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2, default=str))

def create_project_from_query(query):
    """Create a new project via the API based on a query."""
    print_section(f"Creating Project from Query: '{query}'")
    
    project_data = {
        "query": query
    }
    
    response = requests.post(f"{API_BASE_URL}/projects/create-from-query", json=project_data)
    
    if response.status_code == 200:
        project = response.json()
        print("Project created successfully:")
        pretty_print_json(project)
        return project
    else:
        print(f"Error creating project: {response.status_code}")
        print(response.text)
        return None

def explore_project_structure(project_id):
    """Explore the structure of the generated project."""
    print_section("Exploring Project Structure")
    
    # Get the project details
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}")
    
    if response.status_code == 200:
        project = response.json()
        
        # Print project overview
        print("Project Overview:")
        print(f"  Name: {project['name']}")
        print(f"  Description: {project['description']}")
        print(f"  Created: {project['created_at']}")
        print(f"  Teams: {', '.join(project['teams'])}")
        print(f"  Tags: {', '.join(project['tags'])}")
        
        # Print sprint information
        print("\nSprints:")
        for sprint in project['sprints']:
            print(f"  - {sprint['name']}: {sprint['description']}")
            print(f"    Status: {sprint['status']}")
            print(f"    Period: {sprint['start_date']} to {sprint['end_date']}")
            print(f"    Tasks: {len(sprint['todos'])}")
        
        # Print current sprint tasks
        current_sprint = next((s for s in project['sprints'] if s['name'] == project['current_sprint']), None)
        if current_sprint:
            print(f"\nTasks in {current_sprint['name']}:")
            for task in current_sprint['todos']:
                status_marker = "✓" if task['status'] == "DONE" else "□"
                print(f"  {status_marker} {task['title']} (Priority: {task['priority']})")
                print(f"     {task['description']}")
        
        # Print backlog tasks
        if project['todos']:
            print("\nBacklog Tasks:")
            for task in project['todos']:
                status_marker = "✓" if task['status'] == "DONE" else "□"
                print(f"  {status_marker} {task['title']} (Priority: {task['priority']})")
                print(f"     {task['description']}")
        
        return project
    else:
        print(f"Error getting project: {response.status_code}")
        print(response.text)
        return None

def get_todo_markdown(project_id):
    """Get the todo.md file for visualization."""
    print_section("Project Todo Markdown")
    
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}/todo.md")
    
    if response.status_code == 200:
        markdown = response.text
        print(markdown)
        return markdown
    else:
        print(f"Error getting todo.md: {response.status_code}")
        print(response.text)
        return None

def create_job_for_project(project_id, team, query):
    """Create a job for the project."""
    print_section("Creating a Job for the Project")
    
    job_data = {
        "team": team,
        "query": query,
        "project_id": project_id
    }
    
    response = requests.post(f"{API_BASE_URL}/jobs", json=job_data)
    
    if response.status_code == 200:
        job = response.json()
        print("Job created successfully:")
        pretty_print_json(job)
        return job
    else:
        print(f"Error creating job: {response.status_code}")
        print(response.text)
        return None

def main():
    """Run the example workflow."""
    # Create a project from a query
    queries = [
        "Research the latest advances in robotics for healthcare applications",
        "Develop a machine learning model for predictive maintenance",
        "Design a user interface for controlling robotic assistants"
    ]
    
    # Let user select a query or enter a custom one
    print("Select a query to create a project:")
    for i, query in enumerate(queries):
        print(f"{i+1}. {query}")
    print(f"{len(queries)+1}. Enter custom query")
    
    choice = input("\nEnter your choice (1-4): ")
    
    try:
        choice = int(choice)
        if 1 <= choice <= len(queries):
            query = queries[choice-1]
        else:
            query = input("Enter your custom query: ")
    except ValueError:
        query = input("Enter your custom query: ")
    
    # Create a project from the query
    project = create_project_from_query(query)
    if not project:
        print("Failed to create project, exiting.")
        return
    
    project_id = project["id"]
    
    # Explore the created project structure
    project = explore_project_structure(project_id)
    
    # View the todo.md file
    markdown = get_todo_markdown(project_id)
    
    # Create a job associated with the project using the first team
    if project and project['teams']:
        team = project['teams'][0]
        job = create_job_for_project(project_id, team, f"Start working on {project['name']}")
    
    print_section("Example Complete")
    print(f"Project created with ID: {project_id}")
    print("\nTry exploring the project through the API:")
    print(f"- GET {API_BASE_URL}/projects/{project_id}")
    print(f"- GET {API_BASE_URL}/projects/{project_id}/todo.md")

if __name__ == "__main__":
    main() 