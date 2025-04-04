"""
Chat Models

This module defines the core data models for chat functionality.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime


class ChatStatus(str, Enum):
    """Status of a chat conversation."""
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ChatRequest:
    """Request to initiate a chat with the project agent."""
    def __init__(self, query: str, task_id: Optional[str] = None):
        self.query = query
        self.task_id = task_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query": self.query,
            "task_id": self.task_id
        }
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary (compatible with Pydantic models)."""
        return self.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatRequest':
        """Create from dictionary."""
        return cls(
            query=data.get("query", ""),
            task_id=data.get("task_id")
        )


class ChatResponse:
    """Response from chat service."""
    def __init__(
        self,
        conversation_id: str,
        message: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        status: str = "completed",
        project_details: Optional[Dict[str, Any]] = None
    ):
        self.conversation_id = conversation_id
        self.message = message
        self.project_id = project_id
        self.task_id = task_id
        self.status = status
        self.project_details = project_details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "conversation_id": self.conversation_id,
            "message": self.message,
            "status": self.status.value if hasattr(self.status, 'value') else self.status
        }
        
        if self.project_id:
            result["project_id"] = self.project_id
        
        if self.task_id:
            result["task_id"] = self.task_id
            
        if self.project_details:
            result["project_details"] = self.project_details
            
        return result
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary (compatible with Pydantic models)."""
        return self.to_dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatResponse':
        """Create from dictionary."""
        return cls(
            conversation_id=data.get("conversation_id", ""),
            message=data.get("message", ""),
            project_id=data.get("project_id"),
            task_id=data.get("task_id"),
            status=data.get("status", "completed"),
            project_details=data.get("project_details")
        ) 