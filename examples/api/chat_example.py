#!/usr/bin/env python
"""
RoboCo Chat API Example

This script demonstrates how to use the RoboCo Chat API to create projects
by sending a natural language query to the /api/chat endpoint.

The script shows:
1. Initiating a chat with a query
2. Receiving project details from the response
3. Checking the status of an ongoing conversation
4. Creating jobs linked to the generated project
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# API server settings
BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 2  # seconds

def print_section(title):
    """Print a section heading."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def pretty_print_json(data):
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2, default=str))

def chat_with_project_agent(query: str, teams: Optional[list] = None) -> Dict[str, Any]:
    """Send a query to the project agent via the chat API.
    
    Args:
        query: The natural language query
        teams: Optional list of specific teams to assign
        
    Returns:
        The API response with conversation ID and project details
    """
    print_section(f"SENDING QUERY: {query}")
    
    # Prepare request data
    request_data = {
        "query": query
    }
    if teams:
        request_data["teams"] = teams
    
    # Send request to chat API
    response = requests.post(f"{BASE_URL}/api/chat", json=request_data)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return {}
    
    # Parse and display response
    result = response.json()
    print("\nResponse received:")
    print(f"Conversation ID: {result.get('conversation_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    
    # Display project details if available
    if result.get('project_id'):
        print(f"\nProject ID: {result.get('project_id')}")
        if result.get('project_details'):
            print("\nProject Details:")
            pretty_print_json(result.get('project_details'))
    
    return result

def get_chat_status(conversation_id: str) -> Dict[str, Any]:
    """Get the status of a chat conversation.
    
    Args:
        conversation_id: The ID of the conversation to check
        
    Returns:
        The API response with conversation status
    """
    print_section(f"CHECKING CONVERSATION: {conversation_id}")
    
    # Send request to get conversation status
    response = requests.get(f"{BASE_URL}/api/chat/{conversation_id}")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return {}
    
    # Parse and display response
    result = response.json()
    print("\nConversation Status:")
    print(f"Status: {result.get('status')}")
    print(f"Message: {result.get('message')}")
    
    # Display project details if available
    if result.get('project_id'):
        print(f"\nProject ID: {result.get('project_id')}")
        if result.get('project_details'):
            print("\nProject Details:")
            pretty_print_json(result.get('project_details'))
    
    return result

def create_job_for_project(project_id: str, query: str, team: str = "research_team") -> Dict[str, Any]:
    """Create a job linked to the generated project.
    
    Args:
        project_id: The ID of the project to link the job to
        query: The query for the job
        team: The team to use for the job
        
    Returns:
        The API response with job details
    """
    print_section(f"CREATING JOB FOR PROJECT: {project_id}")
    
    # Prepare job request data
    job_data = {
        "team": team,
        "query": query,
        "project_id": project_id
    }
    
    # Send request to create job
    response = requests.post(f"{BASE_URL}/jobs", json=job_data)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return {}
    
    # Parse and display response
    result = response.json()
    print("\nJob Created:")
    print(f"Job ID: {result.get('job_id')}")
    print(f"Status: {result.get('status')}")
    print(f"Team: {result.get('team')}")
    print(f"Query: {result.get('query')}")
    print(f"Project ID: {result.get('project_id')}")
    
    return result

def main():
    """Run the Chat API example."""
    print_section("RoboCo Chat API Example")
    
    # Sample queries for different project types
    sample_queries = [
        "Research the latest advances in quantum computing",
        "Develop a mobile app for tracking health metrics",
        "Design a user interface for an online education platform",
    ]
    
    # Let user select a query or enter a custom one
    print("Select a query to send to the project agent:")
    for i, query in enumerate(sample_queries):
        print(f"{i+1}. {query}")
    print(f"{len(sample_queries)+1}. Enter custom query")
    
    choice = input("\nEnter your choice (1-4): ")
    
    try:
        choice = int(choice)
        if 1 <= choice <= len(sample_queries):
            query = sample_queries[choice-1]
        else:
            query = input("Enter your custom query: ")
    except ValueError:
        query = input("Enter your custom query: ")
    
    # Send the query to the chat API
    result = chat_with_project_agent(query)
    
    # Check if we got a valid result
    if not result:
        print("Failed to get a response from the chat API.")
        return
    
    # Get conversation ID and project ID
    conversation_id = result.get("conversation_id")
    project_id = result.get("project_id")
    
    if not conversation_id:
        print("No conversation ID received.")
        return
    
    # If the conversation is still active, check its status
    if result.get("status") == "active":
        print("\nConversation is still active. Checking status...")
        time.sleep(POLL_INTERVAL)
        result = get_chat_status(conversation_id)
    
    # If we have a project ID, create a job for it
    if project_id:
        print("\nCreating a job for the project...")
        
        # Let user enter a job query
        job_query = input("\nEnter a query for the job (or press Enter for default): ")
        if not job_query:
            job_query = f"Start working on the tasks for project {project_id}"
        
        job_result = create_job_for_project(project_id, job_query)
        
        if job_result:
            print("\nJob created successfully!")
    
    print_section("Example Complete")
    print("You can now:")
    print(f"1. Check the status of your conversation: GET /api/chat/{conversation_id}")
    if project_id:
        print(f"2. View project details: GET /projects/{project_id}")
        print(f"3. View project todo list: GET /projects/{project_id}/todo.md")
    
if __name__ == "__main__":
    main() 