"""Agent system for RoboCo."""

from .base import RoboCoAgent
from .manager import AgentManager
from .roles import HumanAgent, ExecutiveBoardAgent, ProductManagerAgent

__all__ = [
    "RoboCoAgent",
    "AgentManager",
    "HumanAgent",
    "ExecutiveBoardAgent",
    "ProductManagerAgent",
]
