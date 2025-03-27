"""
Roboco Configuration Models

This module defines all configuration models for the Roboco application.
It consolidates the various configuration classes previously spread across multiple files.
"""

from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseModel, Field, model_validator


class ToolConfig(BaseModel):
    """Base configuration for tools."""
    enabled: bool = Field(default=True, description="Whether this tool is enabled")
    name: Optional[str] = Field(None, description="Optional name override for the tool")
    description: Optional[str] = Field(None, description="Optional description override for the tool")
    
    class Config:
        extra = 'allow'  # Allow extra fields for tool-specific configurations


class LLMConfig(BaseModel):
    """Configuration for language model settings."""
    
    model: str = Field(
        default="gpt-4",
        description="The model to use for language generation"
    )
    api_key: str = Field(
        default="",
        description="API key for the language model provider"
    )
    base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the language model API"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for text generation"
    )
    max_tokens: int = Field(
        default=4000,
        gt=0,
        description="Maximum number of tokens to generate"
    )
    terminate_msg: str = Field(
        default="TERMINATE",
        description="Message used by agents to signal completion"
    )
    
    # Optional model-specific configurations
    vision: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for vision-capable models"
    )
    openai: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for OpenAI models"
    )
    deepseek: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for DeepSeek models"
    )
    ollama: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for local Ollama models"
    )
    
    class Config:
        extra = 'allow'  # Allow extra fields for model-specific configurations


class TeamConfig(BaseModel):
    """Configuration for a team of agents.
    
    This standardizes team configuration across different team types.
    Tasks are implemented directly within each team class rather than
    being configured here, to simplify the configuration structure.
    """
    name: str = Field(
        default="",
        description="Name of the team"
    )
    description: str = Field(
        default="",
        description="Description of the team's purpose"
    )
    roles: List[str] = Field(
        default_factory=list,
        description="List of roles in this team"
    )
    orchestrator_name: Optional[str] = Field(
        default=None,
        description="Name of the agent to use as orchestrator (if any)"
    )
    tool_executor: Optional[str] = Field(
        default=None,
        description="Name of the agent to use as tool executor"
    )
    workflow: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Definition of the agent workflow/handoffs"
    )
    tools: List[str] = Field(
        default_factory=list,
        description="List of tools available to the team"
    )
    agent_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Configurations for specific agents in the team"
    )
    output_dir: str = Field(
        default="workspace/team_output",
        description="Directory for team outputs"
    )
    
    class Config:
        extra = 'allow'  # Allow extra fields for team-specific configs


class RoleConfig(BaseModel):
    """Configuration for a specific agent role."""
    
    name: str = Field(
        description="The display name of the role"
    )
    type: str = Field(
        default="agent",
        description="The type of agent (agent or human_proxy)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Description of the role's purpose and capabilities"
    )
    llm: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Role-specific LLM configuration"
    )
    tools: Optional[List[str]] = Field(
        default=None,
        description="List of tool IDs this role has access to"
    )
    
    class Config:
        extra = 'allow'  # Allow extra fields for role-specific configurations


class AgentConfig(BaseModel):
    """Configuration for agent creation and behavior."""
    
    name: str = Field(
        description="The name of the agent"
    )
    role_key: str = Field(
        description="The key of the role this agent fulfills"
    )
    system_message: Optional[str] = Field(
        default=None,
        description="Custom system message for the agent (overrides role's default)"
    )
    llm_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Agent-specific LLM configuration (overrides role's)"
    )
    tool_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for the agent's tools"
    )
    code_execution_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Configuration for code execution (for human proxies)"
    )
    
    class Config:
        extra = 'allow'  # Allow extra fields for custom agent configurations


class CoreConfig(BaseModel):
    """
    Core configuration settings for the application.
    
    This includes settings for databases, caching, storage, and other
    infrastructure components.
    """
    
    # Database settings
    database: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "sqlite",
            "path": "data/roboco.db",
            "pool_size": 5,
            "pool_recycle": 3600,
            "echo": False
        },
        description="Database configuration settings"
    )
    
    # Cache settings
    cache: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "memory",
            "ttl": 3600,  # Time to live in seconds
            "max_size": 1000  # Maximum number of items in cache
        },
        description="Cache configuration settings"
    )
    
    # Storage settings
    storage: Dict[str, Any] = Field(
        default_factory=lambda: {
            "type": "local",
            "root_dir": "data/storage",
            "max_size_mb": 1024
        },
        description="Storage configuration settings"
    )
    
    # Security settings
    security: Dict[str, Any] = Field(
        default_factory=lambda: {
            "secret_key": "",
            "token_expire_minutes": 1440,  # 24 hours
            "algorithm": "HS256"
        },
        description="Security configuration settings"
    )
    
    # Concurrency settings
    concurrency: Dict[str, Any] = Field(
        default_factory=lambda: {
            "max_workers": 4,
            "timeout": 300  # seconds
        },
        description="Concurrency and threading settings"
    )
    
    # Feature flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "enable_web_search": True,
            "enable_code_execution": True,
            "enable_file_access": True,
            "enable_swarm": True
        },
        description="Feature flags for enabling/disabling functionality"
    )
    
    class Config:
        """Pydantic configuration"""
        arbitrary_types_allowed = True
        extra = "allow"  # Allow extra fields


class CompanyConfig(BaseModel):
    """
    Company-specific configuration settings.
    
    This includes information about the company, branding, and
    communication preferences.
    """
    
    # Company info
    name: str = Field(
        default="My Company",
        description="The name of the company"
    )
    description: str = Field(
        default="",
        description="A brief description of the company"
    )
    website: str = Field(
        default="https://example.com",
        description="Company website URL"
    )
    
    # Contact info
    contact_email: str = Field(
        default="contact@example.com",
        description="General contact email for the company"
    )
    support_email: str = Field(
        default="support@example.com",
        description="Support contact email"
    )
    
    # Branding
    logo_path: str = Field(
        default="",
        description="Path to company logo image"
    )
    primary_color: str = Field(
        default="#007BFF",  # Bootstrap primary blue
        description="Primary brand color in hex format"
    )
    secondary_color: str = Field(
        default="#6C757D",  # Bootstrap secondary gray
        description="Secondary brand color in hex format"
    )
    
    # Communication preferences
    email_signature: str = Field(
        default="",
        description="Standard email signature for communications"
    )
    email_templates: Dict[str, str] = Field(
        default_factory=dict,
        description="Email templates for various types of communications"
    )
    
    # Company-specific integrations
    integrations: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Company-specific integrations like CRM, ERP, etc."
    )
    
    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow extra fields


class ProjectConfig(BaseModel):
    """
    Project configuration settings.
    
    This includes metadata, team assignments, and other project-specific settings.
    """
    
    # Project metadata
    name: str = Field(
        default="",
        description="The name of the project"
    )
    description: str = Field(
        default="",
        description="A description of the project"
    )
    created_at: str = Field(
        default="",
        description="When the project was created (ISO format)"
    )
    updated_at: str = Field(
        default="",
        description="When the project was last updated (ISO format)"
    )
    
    # Project organization
    team_ids: List[str] = Field(
        default_factory=list,
        description="IDs of teams assigned to this project"
    )
    owner_id: str = Field(
        default="",
        description="ID of the user who owns the project"
    )
    collaborator_ids: List[str] = Field(
        default_factory=list,
        description="IDs of users collaborating on the project"
    )
    
    # Project settings
    settings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Project-specific settings"
    )
    
    # Project storage
    storage_path: str = Field(
        default="",
        description="Path to project storage directory"
    )
    
    # Project state
    is_active: bool = Field(
        default=True,
        description="Whether the project is active"
    )
    
    class Config:
        """Pydantic configuration"""
        extra = "allow"  # Allow extra fields


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