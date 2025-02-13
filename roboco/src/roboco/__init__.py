"""RoboCo - Multi-Agent System for Humanoid Robot Development."""

__version__ = "0.1.0"

from .core.config import load_config
from .core.types import AgentRole
from .agents.base import RoboCoAgent
from .agents.manager import AgentManager

__all__ = [
    "load_config",
    "AgentRole",
    "RoboCoAgent",
    "AgentManager",
] 