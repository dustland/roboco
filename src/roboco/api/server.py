#!/usr/bin/env python
"""
RoboCo API Server

This module implements the main API server for RoboCo, providing endpoints to:
1. Trigger work processes with various teams
2. Retrieve the status of ongoing work
3. Access generated artifacts and results
4. Manage projects, todos, and sprints
"""

import os
import asyncio
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from roboco.core import TeamBuilder, config
from roboco.core.project_manager import ProjectManager
from roboco.core.schema import TodoItem as CoreTodoItem, Sprint as CoreSprint, ProjectConfig
from roboco.tools import FileSystemTool, BrowserUseTool, WebSearchTool, TerminalTool

from .api_schema import (
    JobRequest, JobStatus, TeamInfo, ArtifactInfo, 
    AgentStatusUpdate, ToolRegistration,
    Project, ProjectCreate, ProjectUpdate, 
    Sprint, SprintCreate, SprintUpdate,
    TodoItem, TodoItemCreate, TodoItemUpdate
)

# Create FastAPI app
app = FastAPI(
    title="RoboCo API",
    description="API for RoboCo - Robot Company driven by AI Agent Teams",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load configuration
app_config = config.load_config()
workspace_dir = app_config.core.workspace_base
os.makedirs(workspace_dir, exist_ok=True)

# Job storage (in-memory for now, could be replaced with a database)
jobs: Dict[str, Dict[str, Any]] = {}  # job_id -> job_info

# Create ProjectManager
project_manager = ProjectManager()

# Background job handling
async def run_team_job(job_id: str, team_key: str, initial_agent: str, query: str, 
                     output_dir: str, parameters: Optional[Dict[str, Any]] = None,
                     project_id: Optional[str] = None):
    """Run a team job in the background."""
    try:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["current_agent"] = initial_agent
        jobs[job_id]["last_updated"] = datetime.now()
        
        # Create team
        team = TeamBuilder.create_team(team_key, output_dir=output_dir)
        
        # Get the executor agent (typically human_proxy)
        executor = team.get_agent("human_proxy")
        
        # Register tools with executor
        fs_tool = FileSystemTool()
        web_tool = WebSearchTool()
        browser_tool = BrowserUseTool()
        
        executor.register_tool(fs_tool)
        executor.register_tool(web_tool)
        executor.register_tool(browser_tool)
        
        # Optional: add more specialized tools based on team type
        if team_key == "development":
            term_tool = TerminalTool()
            executor.register_tool(term_tool)
        
        # Start the team's work
        result = await team.run_swarm(
            initial_agent_name=initial_agent,
            query=query,
            **(parameters or {})
        )
        
        # Update job status
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["end_time"] = datetime.now()
        jobs[job_id]["result"] = result
        jobs[job_id]["last_updated"] = datetime.now()
        jobs[job_id]["progress"] = 1.0
        
        # Save result to output directory
        result_path = os.path.join(workspace_dir, output_dir, "result.json")
        with open(result_path, "w") as f:
            json.dump(result, f, default=str, indent=2)
        
        # Update project if associated with one
        if project_id:
            project_manager.add_job_to_project(project_id, job_id)
        
    except Exception as e:
        # Handle errors
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["end_time"] = datetime.now()
        jobs[job_id]["last_updated"] = datetime.now()
        
        # Log the error to a file
        error_path = os.path.join(workspace_dir, output_dir, "error.txt")
        with open(error_path, "w") as f:
            f.write(f"Error: {str(e)}\n")

# Dependency for getting team configuration
def get_team_config(team_key: str) -> Dict[str, Any]:
    """Get team configuration or raise 404 if not found."""
    try:
        return TeamBuilder.get_instance().get_team_config(team_key)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Team '{team_key}' not found: {str(e)}")

# API Routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to RoboCo API", 
        "documentation": "/docs",
        "status": "operational",
        "api_version": "0.1.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/teams", response_model=List[TeamInfo])
async def list_teams():
    """
    List all available teams.
    
    Returns a list of all configured teams with their roles and tools.
    """
    try:
        # Get the TeamBuilder instance and call the instance method
        team_builder = TeamBuilder.get_instance()
        team_keys = team_builder.list_available_teams()
        teams = []
        
        for key in team_keys:
            team_config = team_builder.get_team_config(key)
            teams.append(TeamInfo(
                key=key,
                name=team_config.get("name", key),
                description=team_config.get("description", ""),
                roles=team_config.get("roles", []),
                tools=team_config.get("tools", [])
            ))
        
        return teams
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing teams: {str(e)}")

@app.get("/teams/{team_key}", response_model=TeamInfo)
async def get_team(team_key: str, team_config: Dict[str, Any] = Depends(get_team_config)):
    """
    Get details for a specific team.
    
    Parameters:
    - team_key: The unique identifier for the team
    
    Returns detailed information about the specified team.
    """
    return TeamInfo(
        key=team_key,
        name=team_config.get("name", team_key),
        description=team_config.get("description", ""),
        roles=team_config.get("roles", []),
        tools=team_config.get("tools", [])
    )

@app.post("/jobs", response_model=JobStatus)
async def create_job(job_request: JobRequest, background_tasks: BackgroundTasks):
    """
    Create and start a new job.
    
    Parameters:
    - team: Team configuration to use
    - initial_agent: Name of the agent to start the process
    - query: Initial query or instruction to process
    - output_dir: (Optional) Custom output directory name
    - parameters: (Optional) Additional parameters for the team
    - project_id: (Optional) Project ID to associate this job with
    
    Returns the initial job status with a unique job_id.
    """
    try:
        # Verify team exists
        team_config = get_team_config(job_request.team)
        
        # Verify project exists if specified
        if job_request.project_id and not project_manager.get_project(job_request.project_id):
            raise HTTPException(status_code=404, detail=f"Project with ID '{job_request.project_id}' not found")
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create output directory
        output_dir = job_request.output_dir or f"job_{job_id}"
        full_output_path = os.path.join(workspace_dir, output_dir)
        os.makedirs(full_output_path, exist_ok=True)
        
        # Initialize job info
        job_info = {
            "job_id": job_id,
            "team": job_request.team,
            "status": "initializing",
            "start_time": datetime.now(),
            "last_updated": datetime.now(),
            "output_dir": output_dir,
            "initial_agent": job_request.initial_agent,
            "query": job_request.query,
            "current_agent": None,
            "progress": 0.0,
            "project_id": job_request.project_id
        }
        
        # Store job info
        jobs[job_id] = job_info
        
        # Also save job info to the output directory
        job_info_path = os.path.join(full_output_path, "job_info.json")
        with open(job_info_path, "w") as f:
            # Convert datetime objects to strings
            serializable_info = job_info.copy()
            serializable_info["start_time"] = serializable_info["start_time"].isoformat()
            serializable_info["last_updated"] = serializable_info["last_updated"].isoformat()
            json.dump(serializable_info, f, indent=2)
        
        # Save the query to a file
        query_path = os.path.join(full_output_path, "query.txt")
        with open(query_path, "w") as f:
            f.write(job_request.query)
        
        # Start background job
        background_tasks.add_task(
            run_team_job,
            job_id,
            job_request.team,
            job_request.initial_agent,
            job_request.query,
            output_dir,
            job_request.parameters,
            job_request.project_id
        )
        
        return JobStatus(**job_info)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle any other exceptions
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

@app.get("/jobs", response_model=List[JobStatus])
async def list_jobs(status: Optional[str] = Query(None, description="Filter by status")):
    """
    List all jobs or filter by status.
    
    Parameters:
    - status: (Optional) Filter jobs by status (running, completed, failed)
    
    Returns a list of job statuses.
    """
    try:
        result = []
        for job_id, job_info in jobs.items():
            if status is None or job_info["status"] == status:
                result.append(JobStatus(**job_info))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing jobs: {str(e)}")

@app.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job(job_id: str):
    """
    Get details for a specific job.
    
    Parameters:
    - job_id: The unique identifier for the job
    
    Returns detailed status information about the specified job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return JobStatus(**jobs[job_id])

@app.patch("/jobs/{job_id}/status")
async def update_job_status(job_id: str, update: AgentStatusUpdate):
    """
    Update the status of a job.
    
    Parameters:
    - job_id: The unique identifier for the job
    - current_agent: The name of the agent currently handling the job
    - progress: (Optional) Progress value between 0.0 and 1.0
    - status_message: (Optional) A message describing the current status
    
    Returns the updated job status.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Verify job_id matches
    if job_id != update.job_id:
        raise HTTPException(status_code=400, detail="Job ID in path must match job ID in request body")
    
    # Update job info
    jobs[job_id]["current_agent"] = update.current_agent
    if update.progress is not None:
        jobs[job_id]["progress"] = update.progress
    jobs[job_id]["last_updated"] = datetime.now()
    
    # Optionally save status message to a log file
    if update.status_message:
        status_log_path = os.path.join(workspace_dir, jobs[job_id]["output_dir"], "status_log.txt")
        with open(status_log_path, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] [{update.current_agent}] {update.status_message}\n")
    
    return JobStatus(**jobs[job_id])

@app.get("/jobs/{job_id}/artifacts", response_model=List[ArtifactInfo])
async def list_artifacts(job_id: str, path: str = ""):
    """
    List artifacts for a specific job.
    
    Parameters:
    - job_id: The unique identifier for the job
    - path: (Optional) Path within the job directory to list artifacts from
    
    Returns a list of artifacts (files and directories) for the job.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    try:
        job_output_dir = os.path.join(workspace_dir, jobs[job_id]["output_dir"])
        target_dir = os.path.join(job_output_dir, path).rstrip("/")
        
        if not os.path.exists(target_dir):
            raise HTTPException(status_code=404, detail=f"Path {path} not found")
        
        if not os.path.isdir(target_dir):
            raise HTTPException(status_code=400, detail=f"Path {path} is not a directory")
        
        artifacts = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            rel_path = os.path.join(path, item).lstrip("/") if path else item
            stat = os.stat(item_path)
            
            artifact = ArtifactInfo(
                name=item,
                path=rel_path,
                size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                type="directory" if os.path.isdir(item_path) else "file"
            )
            artifacts.append(artifact)
        
        return artifacts
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing artifacts: {str(e)}")

@app.get("/jobs/{job_id}/artifacts/{artifact_path:path}")
async def get_artifact(job_id: str, artifact_path: str):
    """
    Get a specific artifact file.
    
    Parameters:
    - job_id: The unique identifier for the job
    - artifact_path: Path to the artifact file within the job directory
    
    Returns the file contents as a download.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    try:
        job_output_dir = os.path.join(workspace_dir, jobs[job_id]["output_dir"])
        file_path = os.path.join(job_output_dir, artifact_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_path} not found")
        
        if os.path.isdir(file_path):
            raise HTTPException(status_code=400, detail=f"Artifact {artifact_path} is a directory, not a file")
        
        return FileResponse(file_path, filename=os.path.basename(file_path))
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving artifact: {str(e)}")

@app.post("/jobs/{job_id}/tools")
async def register_tool(job_id: str, registration: ToolRegistration):
    """
    Register a tool with an agent for a specific job.
    
    Parameters:
    - job_id: The unique identifier for the job
    - tool_name: The name of the tool to register
    - agent_name: The name of the agent to register the tool with
    - parameters: (Optional) Tool initialization parameters
    
    Returns success status.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    try:
        # In a real implementation, this would interact with the running job
        # For now, just return success
        return {"status": "success", "message": f"Tool {registration.tool_name} registered with {registration.agent_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering tool: {str(e)}")

# Route to serve static files for a job
@app.get("/jobs/{job_id}/files/{file_path:path}")
async def serve_static_file(job_id: str, file_path: str):
    """Serve a static file from the job's output directory."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    try:
        job_output_dir = os.path.join(workspace_dir, jobs[job_id]["output_dir"])
        file_path = os.path.join(job_output_dir, file_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found")
        
        return FileResponse(file_path)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

# Mount static files for the workspace directory
app.mount("/workspace", StaticFiles(directory=workspace_dir), name="workspace")

# Project-related API Routes
@app.get("/projects", response_model=List[Project])
async def list_projects():
    """
    List all projects.
    
    Returns a list of all configured projects.
    """
    try:
        # Get simplified list from project manager
        projects_list = project_manager.list_projects()
        projects = []
        
        for project_info in projects_list:
            project_id = project_info["id"]
            project = project_manager.get_project(project_id)
            
            if project:
                # Convert to API response model using helper method
                projects.append(Project.from_core_model(project, project_id))
        
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing projects: {str(e)}")

@app.post("/projects", response_model=Project)
async def create_project(project_create: ProjectCreate):
    """
    Create a new project.
    
    Parameters:
    - name: Name of the project
    - description: Description of the project
    - directory: Optional custom directory name
    - teams: Optional list of team keys
    - tags: Optional tags
    
    Returns the created project.
    """
    try:
        # Create the project
        project_id = project_manager.create_project(
            name=project_create.name,
            description=project_create.description,
            directory=project_create.directory,
            teams=project_create.teams,
            tags=project_create.tags,
            source_code_dir=project_create.source_code_dir,
            docs_dir=project_create.docs_dir
        )
        
        # Get the created project
        project = project_manager.get_project(project_id)
        
        # Convert to API response model using helper method
        return Project.from_core_model(project, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """
    Get a project by ID.
    
    Parameters:
    - project_id: ID of the project
    
    Returns the project.
    """
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found")
    
    # Convert to API response model using helper method
    return Project.from_core_model(project, project_id)

@app.patch("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project_update: ProjectUpdate):
    """
    Update a project.
    
    Parameters:
    - project_id: ID of the project to update
    - project_update: Fields to update
    
    Returns the updated project.
    """
    # Extract non-None fields
    updates = {k: v for k, v in project_update.model_dump().items() if v is not None}
    
    # Update the project
    success = project_manager.update_project(project_id, **updates)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found")
    
    # Return the updated project
    return await get_project(project_id)

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    Delete a project.
    
    Parameters:
    - project_id: ID of the project to delete
    
    Returns a success message.
    """
    success = project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found")
    
    return {"message": f"Project with ID '{project_id}' deleted successfully"}

@app.get("/projects/{project_id}/todo.md")
async def get_todo_markdown(project_id: str):
    """
    Get the todo.md file for a project.
    
    Parameters:
    - project_id: ID of the project
    
    Returns the todo.md file.
    """
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found")
    
    todo_path = os.path.join(project_manager.projects_dir, project_id, "todo.md")
    if not os.path.exists(todo_path):
        # Generate the todo.md file if it doesn't exist
        project_manager._update_todo_markdown(project_id)
    
    if not os.path.exists(todo_path):
        raise HTTPException(status_code=404, detail="todo.md file not found")
    
    return FileResponse(todo_path)

# Todo-related API Routes
@app.post("/projects/{project_id}/todos", response_model=TodoItem)
async def create_todo(project_id: str, todo_create: TodoItemCreate):
    """
    Create a new todo item.
    
    Parameters:
    - project_id: ID of the project
    - todo_create: Todo item data
    
    Returns the created todo item.
    """
    todo = project_manager.create_todo(
        project_id=project_id,
        title=todo_create.title,
        description=todo_create.description,
        status=todo_create.status,
        assigned_to=todo_create.assigned_to,
        priority=todo_create.priority,
        depends_on=todo_create.depends_on,
        tags=todo_create.tags,
        sprint_name=todo_create.sprint_name
    )
    
    if not todo:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found")
    
    # Generate a unique ID for the todo
    todo_id = f"{project_id}_{'sprint_' + todo_create.sprint_name if todo_create.sprint_name else 'backlog'}_{todo.title}"
    
    # Convert to API response model using helper method
    return TodoItem.from_core_model(
        todo=todo,
        todo_id=todo_id,
        sprint_name=todo_create.sprint_name,
        project_id=project_id
    )

@app.patch("/projects/{project_id}/todos/{todo_title}", response_model=TodoItem)
async def update_todo(project_id: str, todo_title: str, todo_update: TodoItemUpdate):
    """
    Update a todo item.
    
    Parameters:
    - project_id: ID of the project
    - todo_title: Title of the todo to update
    - todo_update: Fields to update
    
    Returns the updated todo item.
    """
    # Extract non-None fields
    updates = {k: v for k, v in todo_update.model_dump().items() if v is not None}
    
    # Update the todo
    success = project_manager.update_todo(project_id, todo_title, **updates)
    if not success:
        raise HTTPException(status_code=404, detail=f"Todo item '{todo_title}' not found in project '{project_id}'")
    
    # Get the updated project to find the todo
    project = project_manager.get_project(project_id)
    
    # Find the updated todo
    updated_todo = None
    sprint_name = None
    
    # Check in project todos
    for i, todo in enumerate(project.todos):
        if todo.title == todo_title or (todo_update.title and todo.title == todo_update.title):
            updated_todo = todo
            break
    
    # Check in sprint todos
    if not updated_todo:
        for sprint in project.sprints:
            for i, todo in enumerate(sprint.todos):
                if todo.title == todo_title or (todo_update.title and todo.title == todo_update.title):
                    updated_todo = todo
                    sprint_name = sprint.name
                    break
            if updated_todo:
                break
    
    if not updated_todo:
        raise HTTPException(status_code=404, detail=f"Updated todo item not found")
    
    # Generate the todo ID
    todo_id = f"{project_id}_{'sprint_' + sprint_name if sprint_name else 'backlog'}_{updated_todo.title}"
    
    # Convert to API response model using helper method
    return TodoItem.from_core_model(
        todo=updated_todo,
        todo_id=todo_id,
        sprint_name=sprint_name,
        project_id=project_id
    )

# Sprint-related API Routes
@app.post("/projects/{project_id}/sprints", response_model=Sprint)
async def create_sprint(project_id: str, sprint_create: SprintCreate):
    """
    Create a new sprint.
    
    Parameters:
    - project_id: ID of the project
    - sprint_create: Sprint data
    
    Returns the created sprint.
    """
    sprint = project_manager.create_sprint(
        project_id=project_id,
        name=sprint_create.name,
        description=sprint_create.description,
        start_date=sprint_create.start_date,
        end_date=sprint_create.end_date,
        status=sprint_create.status
    )
    
    if not sprint:
        raise HTTPException(status_code=404, detail=f"Project with ID '{project_id}' not found")
    
    # Convert to API response model using helper method
    return Sprint.from_core_model(sprint=sprint, project_id=project_id)

@app.patch("/projects/{project_id}/sprints/{sprint_name}", response_model=Sprint)
async def update_sprint(project_id: str, sprint_name: str, sprint_update: SprintUpdate):
    """
    Update a sprint.
    
    Parameters:
    - project_id: ID of the project
    - sprint_name: Name of the sprint to update
    - sprint_update: Fields to update
    
    Returns the updated sprint.
    """
    # Extract non-None fields
    updates = {k: v for k, v in sprint_update.model_dump().items() if v is not None}
    
    # Update the sprint
    success = project_manager.update_sprint(project_id, sprint_name, **updates)
    if not success:
        raise HTTPException(status_code=404, detail=f"Sprint '{sprint_name}' not found in project '{project_id}'")
    
    # Get the updated project to find the sprint
    project = project_manager.get_project(project_id)
    
    # Find the updated sprint
    updated_sprint = None
    for sprint in project.sprints:
        if sprint.name == sprint_name or (sprint_update.name and sprint.name == sprint_update.name):
            updated_sprint = sprint
            break
    
    if not updated_sprint:
        raise HTTPException(status_code=404, detail=f"Updated sprint not found")
    
    # Get todos for this sprint
    sprint_todos = [
        TodoItem.from_core_model(
            todo=todo,
            todo_id=f"{project_id}_{updated_sprint.name}_{i}",
            sprint_name=updated_sprint.name,
            project_id=project_id
        )
        for i, todo in enumerate(updated_sprint.todos)
    ]
    
    # Convert to API response model using helper method
    return Sprint.from_core_model(
        sprint=updated_sprint, 
        project_id=project_id,
        todos=sprint_todos
    )

if __name__ == "__main__":
    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"Starting RoboCo API server on http://{host}:{port}")
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload
    ) 