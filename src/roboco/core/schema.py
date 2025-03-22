"""
Schema Definitions

This module defines Pydantic schema models for configuration validation and data structures.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from pathlib import Path
from datetime import datetime


class CompanyConfig(BaseModel):
    """Company information configuration."""
    name: str = Field(
        default="Roboco Robotics Corporation",
        description="Name of the company"
    )
    vision: str = Field(
        default="To be the greatest robotics company in the world",
        description="Company vision statement"
    )


class CoreConfig(BaseModel):
    """Core system configuration."""
    workspace_base: str = Field(
        default="./workspace",
        description="Base directory for workspace files"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode for additional logging"
    )
    cache_dir: str = Field(
        default="./cache",
        description="Directory for storing cache data"
    )
    research_output_dir: str = Field(
        default="./research_output",
        description="Directory for research outputs"
    )
    workspace_root: str = Field(
        default="workspace",
        description="Root directory for all roboco work artifacts"
    )


class LoggingConfig(BaseModel):
    """Configuration for logging settings."""
    level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    file: Optional[str] = Field(
        default=None,
        description="Optional file path for logging output"
    )
    console: bool = Field(
        default=True,
        description="Whether to output logs to console"
    )


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


class TodoItem(BaseModel):
    """A single todo item in a project."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description of the task")
    status: str = Field(default="TODO", description="Status of the task (TODO, IN_PROGRESS, DONE)")
    assigned_to: Optional[str] = Field(None, description="Agent or person assigned to the task")
    priority: str = Field(default="medium", description="Priority level (low, medium, high, critical)")
    created_at: datetime = Field(default_factory=datetime.now, description="When the task was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the task was last updated")
    completed_at: Optional[datetime] = Field(None, description="When the task was completed")
    depends_on: List[str] = Field(default_factory=list, description="IDs of tasks this task depends on")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the task")


class Sprint(BaseModel):
    """A sprint or iteration in a project."""
    name: str = Field(..., description="Name of the sprint")
    description: Optional[str] = Field(None, description="Description of the sprint goals")
    start_date: datetime = Field(..., description="Start date of the sprint")
    end_date: datetime = Field(..., description="End date of the sprint")
    status: str = Field(default="planned", description="Status of the sprint (planned, active, completed)")
    todos: List[TodoItem] = Field(default_factory=list, description="Todo items scheduled for this sprint")


class ProjectConfig(BaseModel):
    """Configuration for a project.
    
    A project is a high-level organizational unit that contains goals,
    teams, and artifacts such as source code and documents. It can span 
    multiple jobs and provides a way to track progress over time through
    iterations or sprints.
    """
    name: str = Field(..., description="Name of the project")
    description: str = Field(..., description="Description of the project goals")
    created_at: datetime = Field(default_factory=datetime.now, description="When the project was created")
    updated_at: datetime = Field(default_factory=datetime.now, description="When the project was last updated")
    directory: str = Field(..., description="Directory where project files are stored")
    teams: List[str] = Field(default_factory=list, description="Teams involved in this project")
    jobs: List[str] = Field(default_factory=list, description="Jobs associated with this project")
    sprints: List[Sprint] = Field(default_factory=list, description="Sprints or iterations planned for this project")
    current_sprint: Optional[str] = Field(None, description="Name of the current active sprint")
    todos: List[TodoItem] = Field(default_factory=list, description="Unassigned todo items for the project")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the project")
    source_code_dir: str = Field(default="src", description="Directory for source code within the project directory")
    docs_dir: str = Field(default="docs", description="Directory for documentation within the project directory")
    
    model_config = dict(
        extra='allow'  # Allow extra fields for project-specific configs
    )
    
    def add_todo(self, todo: TodoItem) -> None:
        """Add a todo item to the project.
        
        Args:
            todo: The todo item to add
        """
        self.todos.append(todo)
        self.updated_at = datetime.now()
    
    def add_sprint(self, sprint: Sprint) -> None:
        """Add a sprint to the project.
        
        Args:
            sprint: The sprint to add
        """
        self.sprints.append(sprint)
        self.updated_at = datetime.now()
    
    def get_active_sprint(self) -> Optional[Sprint]:
        """Get the currently active sprint.
        
        Returns:
            The active sprint or None if no sprint is active
        """
        if not self.current_sprint:
            return None
            
        for sprint in self.sprints:
            if sprint.name == self.current_sprint:
                return sprint
                
        return None


class OrgStructureConfig(BaseModel):
    """Configuration for organizational structure."""
    role: str = Field(..., description="Role title")
    responsibilities: List[str] = Field(..., description="List of responsibilities")
    reports_to: Optional[str] = Field(None, description="Role this position reports to")
    manages: Optional[List[str]] = Field(None, description="Roles managed by this position")
    collaborates_with: Optional[List[str]] = Field(None, description="Roles this position collaborates with")
    tools: List[str] = Field(..., description="List of tools available to this role")


class CommunicationConfig(BaseModel):
    """Configuration for communication patterns."""
    enabled: bool = Field(default=True, description="Whether this pattern is enabled")
    features: List[str] = Field(..., description="List of features")
    collaboration_rules: List[str] = Field(..., description="Rules for collaboration")
    feedback_loops: List[str] = Field(..., description="Feedback mechanisms")


class TeamDynamicsConfig(BaseModel):
    """Configuration for team dynamics."""
    decision_making: Dict[str, Any] = Field(..., description="Decision making style and parameters")
    conflict_resolution: Dict[str, Any] = Field(..., description="Conflict resolution approach")
    knowledge_sharing: Dict[str, Any] = Field(..., description="Knowledge sharing practices")


class AgentConfig(BaseModel):
    """Configuration for agent teams."""
    enabled: bool = Field(default=True, description="Whether this team is enabled")
    llm: str = Field(..., description="LLM configuration to use")
    max_conversation_turns: Optional[int] = Field(None, description="Maximum conversation turns")
    max_iterations: Optional[int] = Field(None, description="Maximum iterations for design tasks")
    design_output_dir: Optional[str] = Field(None, description="Directory for design outputs")


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
    
    model_config = dict(
        extra='allow'  # Allow extra fields for team-specific configs
    )


# Base ToolConfig class remains in core as it's used by multiple tools
class ToolConfig(BaseModel):
    """Base configuration for tools."""
    enabled: bool = Field(default=True, description="Whether this tool is enabled")


class ServerConfig(BaseModel):
    """Configuration for the server."""
    host: str = Field(
        default="127.0.0.1",
        description="Host to bind the server to"
    )
    port: int = Field(
        default=5004,
        description="Port to run the server on"
    )
    log_level: str = Field(
        default="info",
        description="Logging level"
    )
    reload: bool = Field(
        default=True,
        description="Whether to enable auto-reload"
    )


class UIConfig(BaseModel):
    """Configuration for the web UI."""
    enabled: bool = Field(
        default=False,
        description="Whether the UI is enabled"
    )
    port: int = Field(
        default=8000,
        description="Port to run the UI on"
    )
    host: str = Field(
        default="127.0.0.1",
        description="Host to bind the UI to"
    )
    theme: str = Field(
        default="system",
        description="UI theme (light/dark/system)"
    )


class RobocoConfig(BaseModel):
    """Root configuration model for roboco.
    
    This model defines the configuration structure for the roboco framework,
    including company information, LLM settings, tool configurations, and agent behavior settings.
    
    The configuration can be loaded from a YAML file using the load_config function.
    Default locations searched for config files include:
    - ./config.yaml
    - config/config.yaml
    - ~/.config/roboco/config.yaml
    - /etc/roboco/config.yaml
    """
    
    company: CompanyConfig = Field(
        default_factory=CompanyConfig,
        description="Company information"
    )
    core: CoreConfig = Field(
        default_factory=CoreConfig,
        description="Core system settings"
    )
    llm: LLMConfig = Field(
        default_factory=LLMConfig,
        description="Language model configuration"
    )
    org_structure: Dict[str, OrgStructureConfig] = Field(
        default_factory=dict,
        description="Organizational structure"
    )
    communication_patterns: Dict[str, CommunicationConfig] = Field(
        default_factory=dict,
        description="Communication patterns"
    )
    team_dynamics: TeamDynamicsConfig = Field(
        default_factory=lambda: TeamDynamicsConfig(
            decision_making={"style": "consensus", "voting_threshold": 0.75},
            conflict_resolution={"style": "collaborative", "escalation_path": ["executive"]},
            knowledge_sharing={"style": "open", "documentation_requirements": "mandatory"}
        ),
        description="Team dynamics settings"
    )
    agents: Dict[str, AgentConfig] = Field(
        default_factory=dict,
        description="Agent team configurations"
    )
    teams: Dict[str, TeamConfig] = Field(
        default_factory=dict,
        description="Team configurations"
    )
    tools: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool configurations"
    )
    server: ServerConfig = Field(
        default_factory=ServerConfig,
        description="Server configuration"
    )
    ui: UIConfig = Field(
        default_factory=UIConfig,
        description="UI configuration"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )
    
    @property
    def workspace_root(self) -> str:
        """Get the workspace root path from core configuration."""
        return self.core.workspace_root
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key with a default fallback.
        
        Args:
            key: The configuration key to retrieve
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or default if not found
        """
        try:
            # Handle nested keys with dots (e.g., "core.workspace_base")
            if "." in key:
                parts = key.split(".")
                value = self
                for part in parts:
                    value = getattr(value, part)
                return value
            return getattr(self, key)
        except (AttributeError, KeyError):
            return default
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "company": {
                    "name": "Roboco Robotics Corporation",
                    "vision": "To be the greatest robotics company in the world"
                },
                "core": {
                    "workspace_base": "./workspace",
                    "debug": False,
                    "cache_dir": "./cache",
                    "research_output_dir": "./research_output",
                    "workspace_root": "workspace"
                },
                "llm": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4000,
                    "api_key": "YOUR_API_KEY"
                },
                "tools": {
                    "web_research": {
                        "timeout": 30,
                        "max_retries": 3,
                        "use_cache": True,
                        "search": {
                            "max_results": 5,
                            "timeout": 30
                        },
                        "browse": {
                            "timeout": 30,
                            "max_retries": 3
                        }
                    }
                }
            }
        } 