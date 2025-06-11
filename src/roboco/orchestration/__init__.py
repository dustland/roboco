"""
Roboco Orchestration Module

This module provides team-based collaboration orchestration for Roboco.
The framework focuses on dynamic agent collaboration rather than rigid workflows.
"""

from .team_manager import TeamManager
from .models import CollaborationResult

__all__ = [
    "TeamManager",
    "CollaborationResult",
]
