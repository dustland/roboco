"""
Core models package.

This module contains all domain models for the application.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union, Type

from pydantic import ConfigDict, BaseModel

from roboco.core.models.message import (
    Message,
    MessageType,
    MessageRole
)

from roboco.core.models.project import (
    Project
)

from roboco.core.models.task import (
    Task
)

from roboco.core.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatStatus
)

from roboco.core.models.config import (
    AgentConfig,
    ModelConfig,
    ProjectConfig,
    RoleConfig,
    TeamConfig,
    ToolConfig,
    LLMConfig,
    RobocoConfig,
    CoreConfig,
    CompanyConfig
)

# Note: API models (ProjectCreate, TaskCreate, etc.) have been moved to roboco.api.models

__all__ = [
    "Message",
    "MessageType",
    "MessageRole",
    "Project",
    "Task",
    "ChatRequest",
    "ChatResponse",
    "ChatStatus",
    "TeamConfig",
    "ToolConfig",
    "AgentConfig",
    "ModelConfig",
    "ProjectConfig",
    "RoleConfig",
    "LLMConfig",
    "RobocoConfig",
    "CoreConfig",
    "CompanyConfig"
]


class BaseModelWithConfig(BaseModel):
    """A base model with additional configuration options."""
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra='ignore',
        populate_by_name=True
    )