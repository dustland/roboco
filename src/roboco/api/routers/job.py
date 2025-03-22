"""
Job Router

This module defines the FastAPI router for job-related endpoints.
It follows the DDD principles by using the domain services through the API service.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

from roboco.services.api_service import ApiService
from roboco.api.schemas.job import JobRequest, JobStatus, TeamInfo, ArtifactInfo, ToolRegistration, AgentStatusUpdate
from roboco.infrastructure.repositories.file_project_repository import FileProjectRepository
from roboco.services.project_service import ProjectService


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
    responses={404: {"description": "Job not found"}},
)


# Dependency to get the API service
async def get_api_service():
    """Get the API service instance."""
    # Create the repository
    repository = FileProjectRepository()
    
    # Create the domain service
    project_service = ProjectService(repository)
    
    # Create the API service
    api_service = ApiService(project_service)
    
    return api_service


@router.post("/", response_model=JobStatus, status_code=201)
async def create_job(
    job_request: JobRequest,
    background_tasks: BackgroundTasks,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Create and start a new job.
    
    Parameters:
    - team: Team key to use for the job
    - query: Natural language query to process
    - initial_agent: Optional specific agent to start with
    - output_dir: Optional custom output directory
    - parameters: Optional parameters for the job
    - project_id: Optional project ID to associate with the job
    
    Returns the created job status.
    """
    try:
        return await api_service.create_job(job_request, background_tasks)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@router.get("/", response_model=List[JobStatus])
async def list_jobs(
    project_id: Optional[str] = None,
    api_service: ApiService = Depends(get_api_service)
):
    """
    List all jobs, optionally filtered by project ID.
    
    Parameters:
    - project_id: Optional project ID to filter jobs by
    
    Returns a list of job statuses.
    """
    try:
        return await api_service.list_jobs(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing jobs: {str(e)}")


@router.get("/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Get the status of a job.
    
    Parameters:
    - job_id: ID of the job to get status for
    
    Returns the job status.
    """
    job_status = await api_service.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    return job_status


@router.delete("/{job_id}", response_model=dict)
async def cancel_job(
    job_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Cancel a running job.
    
    Parameters:
    - job_id: ID of the job to cancel
    
    Returns a success message.
    """
    success = await api_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found or already completed")
    return {"message": f"Job with ID {job_id} cancelled successfully"}


@router.get("/{job_id}/artifacts", response_model=List[ArtifactInfo])
async def list_job_artifacts(
    job_id: str,
    api_service: ApiService = Depends(get_api_service)
):
    """
    List artifacts generated by a job.
    
    Parameters:
    - job_id: ID of the job
    
    Returns a list of artifact information.
    """
    try:
        artifacts = await api_service.list_job_artifacts(job_id)
        return artifacts
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing artifacts: {str(e)}")


@router.post("/{job_id}/status", response_model=dict)
async def update_job_status(
    job_id: str,
    status_update: AgentStatusUpdate,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Update the status of a job.
    
    Parameters:
    - job_id: ID of the job to update
    - status_update: Status update data
    
    Returns a success message.
    """
    try:
        await api_service.update_job_status(job_id, status_update)
        return {"message": "Job status updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating job status: {str(e)}")


@router.get("/teams", response_model=List[TeamInfo])
async def list_teams(
    api_service: ApiService = Depends(get_api_service)
):
    """
    List all available teams.
    
    Returns a list of team information.
    """
    try:
        return await api_service.list_teams()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing teams: {str(e)}")


@router.post("/tools", response_model=dict)
async def register_tool(
    tool_registration: ToolRegistration,
    api_service: ApiService = Depends(get_api_service)
):
    """
    Register a tool with an agent.
    
    Parameters:
    - tool_registration: Tool registration data
    
    Returns a success message.
    """
    try:
        await api_service.register_tool(tool_registration)
        return {"message": f"Tool {tool_registration.tool_name} registered successfully with agent {tool_registration.agent_name}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering tool: {str(e)}")
