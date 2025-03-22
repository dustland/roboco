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
from roboco.core.config import load_config, get_llm_config


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
        self.workspace_dir = os.path.expanduser(self.config.get("workspace_dir", "~/roboco_workspace"))
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
            # Build the team
            team_builder = TeamBuilder.get_instance()
            team = TeamBuilder.create_team(team_key, output_dir=os.path.join(self.jobs_dir, job_id, output_dir))
            
            # Set up the initial agent
            if not initial_agent and hasattr(team, "default_agent"):
                initial_agent = team.default_agent
            
            if not initial_agent:
                # If no initial agent specified, use the first agent
                agents = team.get_agents()
                if agents:
                    initial_agent = next(iter(agents.keys()))
            
            # Update job status with the actual initial agent
            job_status["initial_agent"] = initial_agent
            job_status["current_agent"] = initial_agent
            self._save_jobs_status()
            
            # Start the team with the query
            result = team.start(initial_agent, query, parameters)
            
            # Update job status
            job_status["status"] = "completed"
            job_status["end_time"] = datetime.now().isoformat()
            job_status["last_updated"] = datetime.now().isoformat()
            job_status["result"] = result
            self._save_jobs_status()
            
        except Exception as e:
            logger.error(f"Error running job {job_id}: {str(e)}")
            
            # Update job status
            job_status["status"] = "failed"
            job_status["end_time"] = datetime.now().isoformat()
            job_status["last_updated"] = datetime.now().isoformat()
            job_status["error"] = str(e)
            self._save_jobs_status()
    
    async def list_jobs(self, status_filter: Optional[str] = None, project_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all jobs, optionally filtered by status or project ID.
        
        Args:
            status_filter: Optional status to filter by.
            project_id: Optional project ID to filter by.
            
        Returns:
            List of job status dictionaries.
        """
        result = []
        
        for job_id, job_status in self.jobs_status.items():
            # Apply filters
            if status_filter and job_status.get("status") != status_filter:
                continue
                
            if project_id and job_status.get("project_id") != project_id:
                continue
                
            result.append(job_status)
        
        # Sort by start time (newest first)
        result.sort(key=lambda x: x.get("start_time", ""), reverse=True)
        
        return result
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a specific job.
        
        Args:
            job_id: The ID of the job.
            
        Returns:
            Job status dictionary or None if not found.
        """
        return self.jobs_status.get(job_id)
    
    async def update_job_status(self, job_id: str, current_agent: Optional[str] = None,
                               progress: Optional[float] = None, status_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Update the status of a job.
        
        Args:
            job_id: The ID of the job.
            current_agent: Optional name of the current agent.
            progress: Optional progress value (0.0 to 1.0).
            status_message: Optional status message.
            
        Returns:
            Updated job status dictionary.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        
        # Update fields
        if current_agent:
            job_status["current_agent"] = current_agent
            
        if progress is not None:
            job_status["progress"] = progress
            
        if status_message:
            job_status["status_message"] = status_message
        
        job_status["last_updated"] = datetime.now().isoformat()
        self._save_jobs_status()
        
        return job_status
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.
        
        Args:
            job_id: The ID of the job to cancel.
            
        Returns:
            True if the job was cancelled, False if not found or already completed.
        """
        if job_id not in self.jobs_status:
            return False
        
        job_status = self.jobs_status[job_id]
        
        if job_status["status"] != "running":
            return False
        
        # Update job status
        job_status["status"] = "cancelled"
        job_status["end_time"] = datetime.now().isoformat()
        job_status["last_updated"] = datetime.now().isoformat()
        self._save_jobs_status()
        
        return True
    
    async def list_job_artifacts(self, job_id: str, path: str = "") -> List[Dict[str, Any]]:
        """
        List artifacts for a specific job.
        
        Args:
            job_id: The ID of the job.
            path: Optional path within the job directory.
            
        Returns:
            List of artifact information dictionaries.
            
        Raises:
            ValueError: If the job is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        output_dir = job_status["output_dir"]
        
        # Construct the full path
        job_dir = os.path.join(self.jobs_dir, job_id, output_dir)
        target_path = os.path.join(job_dir, path) if path else job_dir
        
        if not os.path.exists(target_path):
            raise ValueError(f"Path '{path}' not found in job '{job_id}'")
        
        result = []
        
        # List files and directories
        for item in os.listdir(target_path):
            item_path = os.path.join(target_path, item)
            rel_path = os.path.join(path, item) if path else item
            
            # Get item info
            stat = os.stat(item_path)
            
            artifact_info = {
                "name": item,
                "path": rel_path,
                "size": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "type": "directory" if os.path.isdir(item_path) else "file"
            }
            
            result.append(artifact_info)
        
        # Sort directories first, then by name
        result.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))
        
        return result
    
    async def get_job_artifact(self, job_id: str, artifact_path: str) -> str:
        """
        Get the path to a specific artifact file.
        
        Args:
            job_id: The ID of the job.
            artifact_path: Path to the artifact within the job directory.
            
        Returns:
            Full path to the artifact file.
            
        Raises:
            ValueError: If the job or artifact is not found.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        output_dir = job_status["output_dir"]
        
        # Construct the full path
        job_dir = os.path.join(self.jobs_dir, job_id, output_dir)
        artifact_full_path = os.path.join(job_dir, artifact_path)
        
        if not os.path.exists(artifact_full_path) or not os.path.isfile(artifact_full_path):
            raise ValueError(f"Artifact '{artifact_path}' not found in job '{job_id}'")
        
        return artifact_full_path
    
    async def register_tool(self, job_id: str, tool_name: str, agent_name: str, 
                           parameters: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a tool with an agent for a specific job.
        
        Args:
            job_id: The ID of the job.
            tool_name: The name of the tool to register.
            agent_name: The name of the agent to register the tool with.
            parameters: Optional tool initialization parameters.
            
        Returns:
            True if successful.
            
        Raises:
            ValueError: If the job is not found or the tool registration fails.
        """
        if job_id not in self.jobs_status:
            raise ValueError(f"Job '{job_id}' not found")
        
        job_status = self.jobs_status[job_id]
        
        if job_status["status"] != "running":
            raise ValueError(f"Job '{job_id}' is not running")
        
        # TODO: Implement actual tool registration with the running job
        # This would require a way to communicate with the running job
        
        return True
