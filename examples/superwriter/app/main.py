from fastapi import FastAPI, HTTPException
import os
from pathlib import Path
from contextlib import asynccontextmanager

from .models import TaskRequest, TaskResponse
from roboco.orchestration.team_manager import TeamManager
from roboco.core.exceptions import ConfigurationError

# Determine the project root directory to locate the config file
SUPERWRITER_ROOT = Path(__file__).parent.parent
CONFIG_PATH = SUPERWRITER_ROOT / "config" / "team.yaml"

# Global instance of the TeamManager
team_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global team_manager
    try:
        print(f"Loading team configuration from: {CONFIG_PATH}")
        team_manager = TeamManager(config_path=str(CONFIG_PATH))
        print("TeamManager initialized successfully.")
        
        team_info = team_manager.get_team_info()
        print(f"Team assembled with {len(team_info['agents'])} agents: {[agent['name'] for agent in team_info['agents']]}")
        
    except ConfigurationError as e:
        print(f"FATAL: Could not initialize TeamManager: {e}")
        team_manager = None
        raise e
    
    yield
    
    # Shutdown (cleanup if needed)
    print("Shutting down SuperWriter API")

app = FastAPI(
    title="SuperWriter API",
    description="An API to run collaborative multi-agent writing using the Roboco framework.",
    lifespan=lifespan
)


@app.post("/run-task", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    """
    Accepts a writing task and runs it through the collaborative team.
    """
    if team_manager is None:
        raise HTTPException(status_code=503, detail="TeamManager is not available due to a startup error.")

    if not request.task:
        raise HTTPException(status_code=400, detail="Task cannot be empty.")

    try:
        print(f"Starting collaboration for task: {request.task}")
        result = team_manager.start_collaboration(request.task)
        
        if not result.success:
             raise HTTPException(status_code=500, detail=f"Collaboration failed: {result.error_message}")

        # Construct the response
        response = TaskResponse(
            summary=result.summary,
            chat_history=result.chat_history,
            cost=result.cost if result.cost else 0.0
        )
        return response

    except Exception as e:
        print(f"An error occurred during collaboration: {e}")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

@app.get("/team-info")
def get_team_info():
    """Get information about the current team."""
    if team_manager is None:
        raise HTTPException(status_code=503, detail="TeamManager is not available.")
    
    return team_manager.get_team_info()

@app.get("/")
def read_root():
    return {"message": "Welcome to the SuperWriter API powered by Roboco collaborative teams."}
