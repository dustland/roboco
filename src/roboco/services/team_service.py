"""
Team Service

This module provides services for managing teams, including team creation,
configuration, and orchestration.
"""

from typing import Dict, Any, List, Optional
import os
import json
from datetime import datetime
import uuid
from pathlib import Path
from loguru import logger

from roboco.core import TeamBuilder, config
from roboco.core.config import get_workspace, load_config, get_llm_config


class TeamService:
    """
    Service for managing teams and team-related operations.
    
    This service follows the DDD principles by encapsulating team-related
    business logic and providing a clean interface for the API layer.
    """
    
    def __init__(self):
        """Initialize the team service."""
        # Load global configuration
        self.config = load_config()
        
        # Set up workspace directory
        self.workspace_dir = get_workspace()
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Set up jobs directory
        self.jobs_dir = os.path.join(self.workspace_dir, "jobs")
        os.makedirs(self.jobs_dir, exist_ok=True)
        
        # Jobs status tracking
        self.jobs_status_file = os.path.join(self.workspace_dir, "jobs_status.json")
        self.jobs_status = self._load_jobs_status()
    
    def _load_jobs_status(self) -> Dict[str, Any]:
        """Load jobs status from file."""
        if os.path.exists(self.jobs_status_file):
            try:
                with open(self.jobs_status_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading jobs status: {e}")
        return {}
    
    def _save_jobs_status(self):
        """Save jobs status to file."""
        try:
            with open(self.jobs_status_file, "w") as f:
                json.dump(self.jobs_status, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving jobs status: {e}")
    
    async def list_teams(self) -> List[Dict[str, Any]]:
        """
        List all available teams.
        
        Returns:
            List of team information dictionaries.
        """
        team_builder = TeamBuilder.get_instance()
        teams_config = team_builder.teams_config.get("teams", {})
        
        result = []
        for key, team_info in teams_config.items():
            result.append({
                "id": key,
                "name": team_info.get("name", key),
                "description": team_info.get("description", ""),
                "roles": team_info.get("roles", [])
            })
        
        return result
    
    async def get_team(self, team_key: str) -> Dict[str, Any]:
        """
        Get details for a specific team.
        
        Args:
            team_key: The unique identifier for the team.
            
        Returns:
            Team information dictionary.
            
        Raises:
            ValueError: If the team is not found.
        """
        team_builder = TeamBuilder.get_instance()
        teams_config = team_builder.teams_config.get("teams", {})
        
        if team_key not in teams_config:
            raise ValueError(f"Team '{team_key}' not found")
        
        team_info = teams_config[team_key]
        return {
            "key": team_key,
            "name": team_info.get("name", team_key),
            "description": team_info.get("description", ""),
            "roles": team_info.get("roles", {}),
            "tools": team_info.get("tools", [])
        }
    
    async def create_job(self, team_key: str, query: str, initial_agent: Optional[str] = None,
                        output_dir: Optional[str] = None, parameters: Optional[Dict[str, Any]] = None,
                        project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new job for a team.
        
        Args:
            team_key: The team to use for the job.
            query: The query or instruction to process.
            initial_agent: Optional name of the agent to start with.
            output_dir: Optional custom output directory.
            parameters: Optional additional parameters for the job.
            project_id: Optional project ID to associate with the job.
            
        Returns:
            Job status dictionary with job_id.
            
        Raises:
            ValueError: If the team is not found.
        """
        # Validate team exists
        await self.get_team(team_key)
        
        # Generate job ID and create output directory
        job_id = str(uuid.uuid4())
        
        if output_dir:
            # Clean up output_dir to be a valid directory name
            output_dir = "".join(c if c.isalnum() or c in "._- " else "_" for c in output_dir)
            output_dir = output_dir.strip().replace(" ", "_")
        else:
            # Generate a default output directory name based on the team and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"{team_key}_{timestamp}"
        
        job_dir = os.path.join(self.jobs_dir, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Create job status entry
        job_status = {
            "job_id": job_id,
            "team": team_key,
            "status": "created",
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "output_dir": output_dir,
            "initial_agent": initial_agent,
            "query": query,
            "parameters": parameters or {},
            "project_id": project_id
        }
        
        # Save job status
        self.jobs_status[job_id] = job_status
        self._save_jobs_status()
        
        # Save query to file
        query_file = os.path.join(job_dir, "query.txt")
        with open(query_file, "w") as f:
            f.write(query)
        
        return job_status
    
    async def run_job(self, job_id: str) -> None:
        """
        Run a job in the background.
        
        Args:
            job_id: The ID of the job to run.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        team_key = job_status["team"]
        initial_agent = job_status.get("initial_agent")
        query = job_status["query"]
        output_dir = job_status["output_dir"]
        parameters = job_status.get("parameters", {})
        project_id = job_status.get("project_id")
        
        # Update job status
        job_status["status"] = "running"
        job_status["last_updated"] = datetime.now().isoformat()
        self._save_jobs_status()
        
        try:
            # Create the team
            team_builder = TeamBuilder.get_instance()
            team = team_builder.build_team(team_key)
            
            # Set up the output directory
            job_output_dir = os.path.join(self.jobs_dir, job_id, output_dir)
            os.makedirs(job_output_dir, exist_ok=True)
            
            # Set up the team with the output directory
            team.set_output_dir(job_output_dir)
            
            # Add project ID to the team's context if provided
            if project_id:
                team.add_to_context("project_id", project_id)
            
            # Add any additional parameters to the team's context
            for key, value in parameters.items():
                team.add_to_context(key, value)
            
            # Run the team with the query
            if initial_agent:
                # Start with a specific agent
                agent = team.get_agent(initial_agent)
                if not agent:
                    raise ValueError(f"Agent '{initial_agent}' not found in team '{team_key}'")
                
                result = team.run(query, initial_agent=agent)
            else:
                # Let the team decide which agent to start with
                result = team.run(query)
            
            # Update job status with result
            job_status["status"] = "completed"
            job_status["end_time"] = datetime.now().isoformat()
            job_status["result"] = result
            job_status["last_updated"] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            
            # Update job status with error
            job_status["status"] = "failed"
            job_status["error"] = str(e)
            job_status["end_time"] = datetime.now().isoformat()
            job_status["last_updated"] = datetime.now().isoformat()
        
        # Save updated job status
        self._save_jobs_status()
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a job.
        
        Args:
            job_id: The ID of the job.
            
        Returns:
            Job status dictionary.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        return self.jobs_status[job_id]
    
    async def list_jobs(self, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by project ID.
        
        Args:
            project_id: Optional project ID to filter by.
            
        Returns:
            List of job status dictionaries.
        """
        if project_id:
            return [job for job in self.jobs_status.values() 
                   if job.get("project_id") == project_id]
        else:
            return list(self.jobs_status.values())
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running job.
        
        Args:
            job_id: The ID of the job to cancel.
            
        Returns:
            Updated job status dictionary.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        
        if job_status["status"] == "running":
            # Mark the job as cancelled
            job_status["status"] = "cancelled"
            job_status["end_time"] = datetime.now().isoformat()
            job_status["last_updated"] = datetime.now().isoformat()
            self._save_jobs_status()
        
        return job_status
    
    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its associated files.
        
        Args:
            job_id: The ID of the job to delete.
            
        Returns:
            True if the job was deleted, False otherwise.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        
        # Don't allow deleting running jobs
        if job_status["status"] == "running":
            raise ValueError(f"Cannot delete a running job. Cancel it first.")
        
        # Remove the job directory
        job_dir = os.path.join(self.jobs_dir, job_id)
        if os.path.exists(job_dir):
            import shutil
            shutil.rmtree(job_dir)
        
        # Remove the job from the status tracking
        del self.jobs_status[job_id]
        self._save_jobs_status()
        
        return True
    
    async def get_job_output(self, job_id: str) -> Dict[str, Any]:
        """
        Get the output files for a job.
        
        Args:
            job_id: The ID of the job.
            
        Returns:
            Dictionary with file information.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        output_dir = job_status["output_dir"]
        job_dir = os.path.join(self.jobs_dir, job_id)
        job_output_dir = os.path.join(job_dir, output_dir)
        
        # Get list of files in the output directory
        files = []
        if os.path.exists(job_output_dir):
            for root, _, filenames in os.walk(job_output_dir):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, job_output_dir)
                    
                    # Get file stats
                    stats = os.stat(file_path)
                    
                    files.append({
                        "name": filename,
                        "path": rel_path,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                    })
        
        return {
            "job_id": job_id,
            "output_dir": output_dir,
            "files": files
        }
