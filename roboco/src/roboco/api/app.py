import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel
import autogen

from ..agents import TeamManager

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="RoboCo API",
    description="API for RoboCo service",
    version="0.1.0"
)

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    file_location=".",
)

# Initialize the team manager
team_manager = TeamManager(config_list=config_list)  # Autogen will load from OAI_CONFIG_LIST

class VisionRequest(BaseModel):
    """Request model for setting product vision."""
    vision: str

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to RoboCo API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/vision")
async def process_vision(request: VisionRequest) -> Dict[str, Any]:
    """Process a product vision through the multi-agent system."""
    try:
        # Process the vision through the team
        result = team_manager.process_vision(request.vision)
        return result
    except Exception as e:
        logger.error(f"Error processing vision: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing vision: {str(e)}"
        )

def start():
    """Start the RoboCo service."""
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info")
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    uvicorn.run(
        "roboco.api.app:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=reload
    ) 