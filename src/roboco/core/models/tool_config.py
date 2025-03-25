"""
Tool Configuration Models

This module defines configuration models for tools.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Base configuration for tools."""
    enabled: bool = Field(default=True, description="Whether this tool is enabled")
    name: Optional[str] = Field(None, description="Optional name override for the tool")
    description: Optional[str] = Field(None, description="Optional description override for the tool")
    
    class Config:
        extra = 'allow'  # Allow extra fields for tool-specific configurations 