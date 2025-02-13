"""API routes for agent interactions."""

from typing import Dict, List
from fastapi import APIRouter
from loguru import logger

from roboco.core.types import AgentRole
from roboco.agents.manager import AgentManager
from roboco.api.models.messages import MessageRequest, MessageResponse

router = APIRouter(prefix="/agents", tags=["agents"])
agent_manager = AgentManager()

@router.post("/message", response_model=MessageResponse)
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

@router.get("/roles", response_model=List[str])
async def get_available_roles() -> List[str]:
    """Get list of all available agent roles."""
    logger.info("Getting available agent roles")
    return [role.value for role in AgentRole]

@router.get("/status")
async def get_agent_status() -> Dict[str, bool]:
    """Get the status of all agents."""
    logger.info("Checking agent status")
    status = {}
    for role in AgentRole:
        agent = agent_manager.get_agent(role)
        status[role.value] = agent is not None
    return status 