"""
Orchestration Models

This module contains data models for team collaboration results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class CollaborationResult(BaseModel):
    """Result of a team collaboration session."""
    summary: str
    chat_history: List[Dict[str, Any]]
    participants: List[str]
    cost: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None 