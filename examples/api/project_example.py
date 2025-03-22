#!/usr/bin/env python
"""
Project Management Example

This script demonstrates how to use the RoboCo API to manage projects, todos, and sprints.
It shows the process of:
1. Creating a new project
2. Creating a sprint for the project
3. Adding todos to the project and sprint
4. Updating todo status
5. Creating a job associated with the project
6. Retrieving the project's todo.md file
"""

import os
import json
import time
from datetime import datetime, timedelta
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

def create_project():
    """Create a new project via the API."""
    print_section("Creating a New Project")
    
    project_data = {
        "name": "Sample ML Project",
        "description": "A machine learning project to demonstrate RoboCo's project management capabilities",
        "teams": ["research_team"],
        "tags": ["machine-learning", "demo"],
        "source_code_dir": "src",
        "docs_dir": "docs"
    }
    
    response = requests.post(f"{API_BASE_URL}/projects", json=project_data)
    
    if response.status_code == 200:
        project = response.json()
        print("Project created successfully:")
        pretty_print_json(project)
        return project["id"]
    else:
        print(f"Error creating project: {response.status_code}")
        print(response.text)
        return None

def create_sprint(project_id):
    """Create a sprint for a project."""
    print_section("Creating a Sprint")
    
    # Create a sprint starting today and lasting two weeks
    today = datetime.now()
    end_date = today + timedelta(days=14)
    
    sprint_data = {
        "name": "Sprint 1",
        "description": "Initial planning and setup sprint",
        "start_date": today.isoformat(),
        "end_date": end_date.isoformat(),
        "status": "active"
    }
    
    response = requests.post(f"{API_BASE_URL}/projects/{project_id}/sprints", json=sprint_data)
    
    if response.status_code == 200:
        sprint = response.json()
        print("Sprint created successfully:")
        pretty_print_json(sprint)
        return sprint["name"]
    else:
        print(f"Error creating sprint: {response.status_code}")
        print(response.text)
        return None

def create_todo(project_id, title, description, status="TODO", assigned_to=None, sprint_name=None):
    """Create a todo item for a project or sprint."""
    todo_data = {
        "title": title,
        "description": description,
        "status": status,
        "assigned_to": assigned_to,
        "priority": "medium",
        "tags": [],
        "sprint_name": sprint_name
    }
    
    response = requests.post(f"{API_BASE_URL}/projects/{project_id}/todos", json=todo_data)
    
    if response.status_code == 200:
        todo = response.json()
        print(f"Todo '{title}' created successfully:")
        pretty_print_json(todo)
        return todo["id"]
    else:
        print(f"Error creating todo: {response.status_code}")
        print(response.text)
        return None

def update_todo_status(project_id, todo_title, new_status):
    """Update the status of a todo item."""
    update_data = {
        "status": new_status
    }
    
    response = requests.patch(f"{API_BASE_URL}/projects/{project_id}/todos/{todo_title}", json=update_data)
    
    if response.status_code == 200:
        todo = response.json()
        print(f"Todo '{todo_title}' updated successfully:")
        pretty_print_json(todo)
        return True
    else:
        print(f"Error updating todo: {response.status_code}")
        print(response.text)
        return False

def create_job(project_id, team="research_team", query="What are the latest advances in transformer models?"):
    """Create a job associated with a project."""
    print_section("Creating a Job for the Project")
    
    job_data = {
        "team": team,
        "query": query,
        "initial_agent": "ai_researcher",
        "project_id": project_id
    }
    
    response = requests.post(f"{API_BASE_URL}/jobs", json=job_data)
    
    if response.status_code == 200:
        job = response.json()
        print("Job created successfully:")
        pretty_print_json(job)
        return job["job_id"]
    else:
        print(f"Error creating job: {response.status_code}")
        print(response.text)
        return None

def get_todo_markdown(project_id):
    """Get the todo.md markdown file for a project."""
    print_section("Retrieving Todo Markdown")
    
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}/todo.md")
    
    if response.status_code == 200:
        markdown = response.text
        print("Todo.md content:")
        print("-" * 80)
        print(markdown)
        print("-" * 80)
        return markdown
    else:
        print(f"Error getting todo.md: {response.status_code}")
        print(response.text)
        return None

def main():
    """Run the example workflow."""
    # Create a new project
    project_id = create_project()
    if not project_id:
        print("Failed to create project, exiting.")
        return
    
    # Create a sprint for the project
    sprint_name = create_sprint(project_id)
    
    # Create some backlog todos (not in a sprint)
    print_section("Creating Backlog Todos")
    create_todo(
        project_id=project_id,
        title="Research competitive solutions",
        description="Investigate existing solutions in the market and compare their approaches"
    )
    
    create_todo(
        project_id=project_id,
        title="Prepare dataset requirements",
        description="Document the necessary datasets and their properties for the ML model"
    )
    
    # Create some todos in the sprint
    print_section("Creating Sprint Todos")
    create_todo(
        project_id=project_id,
        title="Set up development environment",
        description="Configure the necessary tools and libraries for development",
        sprint_name=sprint_name
    )
    
    create_todo(
        project_id=project_id,
        title="Define initial model architecture",
        description="Design the first version of the ML model architecture",
        sprint_name=sprint_name
    )
    
    # Update a todo status
    print_section("Updating Todo Status")
    update_todo_status(
        project_id=project_id,
        todo_title="Set up development environment",
        new_status="IN_PROGRESS"
    )
    
    # Create a job associated with the project
    job_id = create_job(project_id)
    
    # Retrieve the todo.md file
    get_todo_markdown(project_id)
    
    print_section("Example Complete")
    print(f"Project created with ID: {project_id}")
    if job_id:
        print(f"Job created with ID: {job_id}")
    print("\nTry exploring the project through the API:")
    print(f"- GET {API_BASE_URL}/projects/{project_id}")
    print(f"- GET {API_BASE_URL}/projects/{project_id}/todo.md")

if __name__ == "__main__":
    main() 