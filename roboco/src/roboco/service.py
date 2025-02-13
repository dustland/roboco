"""RoboCo backend service."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from loguru import logger

from .agents.base import AgentRole, AgentConfig, RoboCoAgent
from .agents.manager import AgentManager
from .config import load_config

app = FastAPI(title="RoboCo Backend Service")

# Initialize configuration
config = load_config()
agent_manager = AgentManager()

# Configure logging
logger.add(
    "logs/roboco.log",
    rotation="500 MB",
    retention="10 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    """Request model for sending messages between agents."""
    from_role: AgentRole
    to_role: AgentRole
    message: str

class MessageResponse(BaseModel):
    """Response model for agent messages."""
    response: Optional[str]
    success: bool
    error: Optional[str] = None

@app.post("/agents/message", response_model=MessageResponse)
async def send_message(request: MessageRequest) -> MessageResponse:
    """Send a message between agents."""
    try:
        logger.info(f"Sending message from {request.from_role} to {request.to_role}")
        response = await agent_manager.send_message(
            request.from_role,
            request.to_role,
            request.message
        )
        success = bool(response)
        if not success:
            logger.warning("Failed to get response from agent")
        return MessageResponse(
            response=response,
            success=success,
            error=None if success else "Failed to get response"
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return MessageResponse(
            response=None,
            success=False,
            error=str(e)
        )

@app.get("/agents/roles", response_model=List[str])
async def get_available_roles() -> List[str]:
    """Get list of all available agent roles."""
    logger.info("Getting available agent roles")
    return [role.value for role in AgentRole]

@app.get("/agents/status")
async def get_agent_status() -> Dict[str, bool]:
    """Get the status of all agents."""
    logger.info("Checking agent status")
    status = {}
    for role in AgentRole:
        agent = agent_manager.get_agent(role)
        status[role.value] = agent is not None
    return status

@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    logger.debug("Health check requested")
    return {"status": "healthy"} 