#!/usr/bin/env python
"""
RoboCo API Client Example

This script demonstrates how to interact with the RoboCo API server.
It shows how to:
1. List available teams
2. Create a new job
3. Monitor job progress
4. Access artifacts when the job completes
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# API server settings
BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 2  # seconds

def list_teams() -> List[Dict[str, Any]]:
    """List all available teams."""
    print("\n=== Available Teams ===")
    response = requests.get(f"{BASE_URL}/teams")
    if response.status_code != 200:
        print(f"Error listing teams: {response.text}")
        return []
    
    teams = response.json()
    for team in teams:
        print(f"\n* {team['name']} ({team['key']})")
        print(f"  Description: {team['description']}")
        print(f"  Roles: {', '.join(team['roles'])}")
        print(f"  Tools: {', '.join(team['tools'])}")
    
    return teams

def get_team_details(team_key: str) -> Optional[Dict[str, Any]]:
    """Get details for a specific team."""
    print(f"\n=== Team Details: {team_key} ===")
    response = requests.get(f"{BASE_URL}/teams/{team_key}")
    if response.status_code != 200:
        print(f"Error getting team details: {response.text}")
        return None
    
    team = response.json()
    print(f"Name: {team['name']}")
    print(f"Description: {team['description']}")
    print(f"Roles: {', '.join(team['roles'])}")
    print(f"Tools: {', '.join(team['tools'])}")
    
    return team

def create_job(team_key: str, initial_agent: str, query: str, output_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Create a new job."""
    print(f"\n=== Creating Job ===")
    print(f"Team: {team_key}")
    print(f"Initial Agent: {initial_agent}")
    print(f"Query: {query}")
    
    job_data = {
        "team": team_key,
        "initial_agent": initial_agent,
        "query": query
    }
    
    if output_dir:
        job_data["output_dir"] = output_dir
    
    response = requests.post(f"{BASE_URL}/jobs", json=job_data)
    if response.status_code != 200:
        print(f"Error creating job: {response.text}")
        return None
    
    job = response.json()
    print(f"Job created with ID: {job['job_id']}")
    print(f"Status: {job['status']}")
    print(f"Output directory: {job['output_dir']}")
    
    return job

def monitor_job(job_id: str, wait: bool = True) -> Dict[str, Any]:
    """Monitor a job until it completes or fails."""
    print(f"\n=== Monitoring Job: {job_id} ===")
    
    completed = False
    job = None
    
    while not completed:
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        if response.status_code != 200:
            print(f"Error monitoring job: {response.text}")
            return {}
        
        job = response.json()
        
        # Format start time
        start_time = datetime.fromisoformat(job["start_time"].replace("Z", "+00:00"))
        
        # Print status update
        status_line = f"Status: {job['status']} | Agent: {job.get('current_agent') or 'initializing'}"
        if job.get("progress") is not None:
            status_line += f" | Progress: {job['progress'] * 100:.1f}%"
        
        print(status_line)
        
        if job["status"] in ["completed", "failed"]:
            completed = True
            
            if job["status"] == "completed":
                print("\n✅ Job completed successfully!")
                if job.get("result"):
                    print("\nResult:")
                    print(json.dumps(job["result"], indent=2))
            else:
                print(f"\n❌ Job failed: {job.get('error', 'Unknown error')}")
            
            # Print duration
            if job.get("end_time"):
                end_time = datetime.fromisoformat(job["end_time"].replace("Z", "+00:00"))
                duration = end_time - start_time
                print(f"\nDuration: {duration}")
        
        elif wait:
            print(f"Waiting {POLL_INTERVAL} seconds for updates...")
            time.sleep(POLL_INTERVAL)
        else:
            break
    
    return job

def list_artifacts(job_id: str, path: str = "") -> List[Dict[str, Any]]:
    """List artifacts for a job."""
    print(f"\n=== Artifacts for Job: {job_id} ===")
    if path:
        print(f"Path: {path}")
    
    response = requests.get(f"{BASE_URL}/jobs/{job_id}/artifacts", params={"path": path})
    if response.status_code != 200:
        print(f"Error listing artifacts: {response.text}")
        return []
    
    artifacts = response.json()
    
    # Group by type
    directories = [a for a in artifacts if a["type"] == "directory"]
    files = [a for a in artifacts if a["type"] == "file"]
    
    # Print directories first
    if directories:
        print("\nDirectories:")
        for directory in directories:
            print(f"📁 {directory['name']}")
    
    # Then print files
    if files:
        print("\nFiles:")
        for file in files:
            size_str = f"{file['size']} bytes"
            if file['size'] > 1024:
                size_str = f"{file['size'] / 1024:.1f} KB"
            if file['size'] > 1024 * 1024:
                size_str = f"{file['size'] / (1024 * 1024):.1f} MB"
            print(f"📄 {file['name']} ({size_str})")
    
    if not artifacts:
        print("No artifacts found.")
    
    return artifacts

def download_artifact(job_id: str, artifact_path: str, save_path: Optional[Path] = None) -> bool:
    """Download an artifact."""
    print(f"\n=== Downloading Artifact ===")
    print(f"Job: {job_id}")
    print(f"Artifact: {artifact_path}")
    
    # If save_path is not specified, use the filename from the artifact path
    if save_path is None:
        save_path = Path(os.path.basename(artifact_path))
    
    # Create parent directories if they don't exist
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    response = requests.get(f"{BASE_URL}/jobs/{job_id}/artifacts/{artifact_path}")
    if response.status_code != 200:
        print(f"Error downloading artifact: {response.text}")
        return False
    
    with open(save_path, "wb") as f:
        f.write(response.content)
    
    print(f"Downloaded to: {save_path}")
    return True

def update_job_status(job_id: str, current_agent: str, progress: Optional[float] = None, message: Optional[str] = None) -> bool:
    """Update the status of a job (for testing API)."""
    print(f"\n=== Updating Job Status ===")
    print(f"Job: {job_id}")
    print(f"Agent: {current_agent}")
    if progress is not None:
        print(f"Progress: {progress * 100:.1f}%")
    if message:
        print(f"Message: {message}")
    
    update_data = {
        "job_id": job_id,
        "current_agent": current_agent
    }
    if progress is not None:
        update_data["progress"] = progress
    if message:
        update_data["status_message"] = message
    
    response = requests.patch(f"{BASE_URL}/jobs/{job_id}/status", json=update_data)
    if response.status_code != 200:
        print(f"Error updating job status: {response.text}")
        return False
    
    print("Status updated successfully.")
    return True

def main():
    # List available teams
    teams = list_teams()
    if not teams:
        print("No teams available. Make sure the RoboCo API server is running.")
        return 1
    
    # Get a team to use for the example
    team_key = teams[0]["key"]
    team = get_team_details(team_key)
    if not team:
        print(f"Failed to get details for team: {team_key}")
        return 1
    
    # Choose an initial agent
    initial_agent = team["roles"][0]
    
    # Create a job
    query = "Explore and summarize the current economic impacts of AI technology adoption across different industries."
    job = create_job(team_key, initial_agent, query)
    if not job:
        print("Failed to create job.")
        return 1
    
    # Simulate updating the job status (just for API testing)
    update_job_status(job["job_id"], initial_agent, 0.1, "Starting research process")
    
    # Monitor the job (uncommenting will wait for completion)
    # To avoid waiting for the actual job to complete, we'll just check status once
    job = monitor_job(job["job_id"], wait=False)
    
    # List artifacts
    artifacts = list_artifacts(job["job_id"])
    
    # Download the first file artifact if available
    file_artifacts = [a for a in artifacts if a["type"] == "file"]
    if file_artifacts:
        download_artifact(job["job_id"], file_artifacts[0]["path"])
    
    print("\nExample completed successfully. The job continues to run in the background.")
    print(f"Monitor it by visiting: {BASE_URL}/jobs/{job['job_id']}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 