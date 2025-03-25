"""
Roboco Configuration

This module defines the main configuration schema for the Roboco application.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import BaseModel, Field, model_validator

from roboco.core.models.llm_config import LLMConfig
from roboco.core.models.core_config import CoreConfig
from roboco.core.models.company_config import CompanyConfig


class RobocoConfig(BaseModel):
    """
    Main configuration for the Roboco application.
    
    This is the top-level configuration model that contains all settings for the application.
    """
    
    # Workspace settings
    workspace_root: str = Field(
        default="~/roboco_workspace",
        description="Root directory for all workspaces"
    )
    
    # LLM settings
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="Language model settings"
    )
    
    # Core system settings
    core: CoreConfig = Field(
        default_factory=CoreConfig,
        description="Core system configuration settings"
    )
    
    # Company settings
    company: CompanyConfig = Field(
        default_factory=CompanyConfig,
        description="Company-specific settings"
    )
    
    # Agent settings
    agents: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Agent configurations"
    )
    
    # Team settings
    teams: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Team configurations"
    )
    
    # Logging settings
    logging: Dict[str, Any] = Field(
        default_factory=lambda: {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None
        },
        description="Logging configuration"
    )
    
    # Tool settings
    tools: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Tool configurations"
    )
    
    # API settings
    api: Dict[str, Any] = Field(
        default_factory=lambda: {
            "host": "127.0.0.1",
            "port": 8000,
            "debug": False,
        },
        description="API server configuration"
    )
    
    # Project settings
    projects: Dict[str, Any] = Field(
        default_factory=dict,
        description="Project configurations"
    )
    
    # Additional settings not covered by specific fields
    extras: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional configuration options"
    )

    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra fields
        
    @model_validator(mode='after')
    def validate_workspace_path(self) -> 'RobocoConfig':
        """Validate and normalize the workspace path."""
        if self.workspace_root.startswith('~'):
            # Expand user directory
            self.workspace_root = str(Path(self.workspace_root).expanduser())
        return self 