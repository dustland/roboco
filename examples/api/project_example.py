#!/usr/bin/env python
"""
Project Management Example

This script demonstrates how to use the RoboCo API to manage projects, tasks, and sprints.
It shows the process of:
1. Creating a new project
2. Creating a sprint for the project
3. Adding tasks to the project and sprint
4. Updating task status
5. Creating a job associated with the project
6. Retrieving the project's task.md file
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

def create_task(project_id, title, description, status="TODO", assigned_to=None, sprint_name=None):
    """Create a task item for a project or sprint."""
    print_section(f"Creating Task: {title}")
    
    task_data = {
        "title": title,
        "description": description,
        "status": status,
        "assigned_to": assigned_to,
        "sprint_name": sprint_name,
        "priority": "medium",
        "tags": ["demo"]
    }
    
    response = requests.post(f"{API_BASE_URL}/projects/{project_id}/tasks", json=task_data)
    
    if response.status_code == 201:
        task = response.json()
        print("Task created successfully:")
        pretty_print_json(task)
        return task
    else:
        print(f"Error creating task: {response.status_code}")
        print(response.text)
        return None

def update_task_status(project_id, task_title, new_status):
    """Update the status of a task item."""
    print_section(f"Updating Task Status: {task_title} -> {new_status}")
    
    # First, get the task ID
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}/tasks")
    tasks = response.json()
    task_id = next((task["id"] for task in tasks if task["title"] == task_title), None)
    
    if not task_id:
        print(f"Task with title '{task_title}' not found")
        return None
    
    # Now update the task
    update_data = {"status": new_status}
    response = requests.put(f"{API_BASE_URL}/projects/{project_id}/tasks/{task_id}", json=update_data)
    
    if response.status_code == 200:
        task = response.json()
        print("Task updated successfully:")
        pretty_print_json(task)
        return task
    else:
        print(f"Error updating task: {response.status_code}")
        print(response.text)
        return None

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

def get_task_markdown(project_id):
    """Get the task.md markdown file for a project."""
    print_section("Getting Task Markdown")
    
    response = requests.get(f"{API_BASE_URL}/projects/{project_id}/task-md")
    
    if response.status_code == 200:
        markdown = response.text
        print("Task markdown retrieved successfully:")
        print("\n" + markdown)
        return markdown
    else:
        print(f"Error getting task markdown: {response.status_code}")
        print(response.text)
        return None

def main():
    """Run the example workflow."""
    print_section("RoboCo API Example: Project Management")
    
    # Step 1: Create a project
    project_id = create_project()
    if not project_id:
        print("Failed to create project. Exiting.")
        return
    
    # Step 2: Create a sprint
    sprint = create_sprint(project_id)
    if not sprint:
        print("Failed to create sprint. Exiting.")
        return
    
    # Step 3: Create tasks
    tasks = []
    
    # Task 1: Research task
    research_task = create_task(
        project_id=project_id,
        title="Research transformer models",
        description="Investigate the latest advances in transformer models for NLP",
        status="TODO",
        assigned_to="researcher",
        sprint_name=sprint
    )
    tasks.append(research_task)
    
    # Task 2: Implementation task
    implementation_task = create_task(
        project_id=project_id,
        title="Implement prototype model",
        description="Create a prototype implementation of the selected model architecture",
        status="TODO",
        assigned_to="developer"
    )
    tasks.append(implementation_task)
    
    # Task 3: Documentation task
    documentation_task = create_task(
        project_id=project_id,
        title="Document API",
        description="Create comprehensive API documentation for the model interface",
        status="TODO",
        assigned_to="technical_writer"
    )
    tasks.append(documentation_task)
    
    # Step 4: Update task status
    if research_task:
        updated_task = update_task_status(project_id, research_task["title"], "IN_PROGRESS")
    
    # Step 5: Create a job
    job = create_job(project_id)
    
    # Step 6: Get task markdown
    markdown = get_task_markdown(project_id)
    
    print_section("Example Complete")
    print("The example has completed successfully. You now have:")
    print(f"- A project: {project_id}")
    print(f"- A sprint: {sprint}")
    print(f"- {len(tasks)} tasks")
    print(f"- A job: {job if job else 'None'}")
    print("\nYou can now explore the project through the API or UI.")

if __name__ == "__main__":
    main()