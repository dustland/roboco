"""
Config subsystem models - Self-contained configuration data models.

This module contains all data models related to configuration management, following the
architectural rule that subsystems should be self-contained and not import from core.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from pathlib import Path
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# CONFIGURATION BASE MODELS
# ============================================================================

class ConfigError(Exception):
    """Base exception for configuration errors."""
    pass


class ConfigurationError(ConfigError):
    """Configuration validation or loading error."""
    pass


# ============================================================================
# LLM AND BRAIN CONFIGURATION
# ============================================================================

class LLMProviderConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: str  # "openai", "anthropic", "deepseek", etc.
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 60
    max_retries: int = 3
    
    # Provider-specific settings
    extra_params: Dict[str, Any] = Field(default_factory=dict)


class BrainConfig(BaseModel):
    """Configuration for agent brain (LLM interaction)."""
    llm_config: LLMProviderConfig
    system_message: Optional[str] = None
    max_context_length: int = 8192
    context_strategy: str = "truncate"  # "truncate", "summarize", "sliding_window"
    
    # Function calling settings
    function_calling: bool = True
    parallel_function_calls: bool = True
    max_function_calls_per_turn: int = 10
    
    # Streaming settings
    streaming: bool = False
    stream_chunk_size: int = 1024


# ============================================================================
# AGENT CONFIGURATION
# ============================================================================

class AgentRole(str, Enum):
    """Standard agent roles."""
    COORDINATOR = "coordinator"
    RESEARCHER = "researcher" 
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    SPECIALIST = "specialist"


class AgentConfig(BaseModel):
    """Configuration for individual agents."""
    name: str
    role: Optional[AgentRole] = None
    description: Optional[str] = None
    
    # Brain configuration
    brain_config: BrainConfig
    
    # System message and prompts
    system_message: Optional[str] = None
    prompt_template: Optional[str] = None
    prompt_file: Optional[str] = None
    
    # Tool configuration
    tools: List[str] = Field(default_factory=list)
    tool_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent behavior settings
    max_iterations: int = 10
    timeout: int = 300
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# MEMORY CONFIGURATION
# ============================================================================

class MemoryBackendType(str, Enum):
    """Types of memory backends."""
    MEM0 = "mem0"
    CHROMA = "chroma"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    LOCAL = "local"


class MemoryConfig(BaseModel):
    """Configuration for memory system."""
    enabled: bool = True
    backend: MemoryBackendType = MemoryBackendType.MEM0
    
    # Backend-specific configuration
    config: Dict[str, Any] = Field(default_factory=dict)
    
    # Memory behavior settings
    max_memories: Optional[int] = None
    retention_days: Optional[int] = None
    importance_threshold: float = 0.5
    
    # Synthesis settings
    synthesis_enabled: bool = True
    synthesis_interval: int = 3600  # seconds
    
    # Context injection settings
    context_enabled: bool = True
    max_context_memories: int = 10


# ============================================================================
# STORAGE CONFIGURATION
# ============================================================================

class StorageBackendType(str, Enum):
    """Types of storage backends."""
    LOCAL = "local"
    GIT = "git"
    S3 = "s3"
    AZURE = "azure"
    GCS = "gcs"


class StorageConfig(BaseModel):
    """Configuration for storage system."""
    backend: StorageBackendType = StorageBackendType.LOCAL
    workspace_path: str = "./workspace"
    
    # Git-specific settings
    git_enabled: bool = True
    auto_commit: bool = True
    commit_message_template: str = "AgentX: {action} by {agent}"
    
    # Cloud storage settings (if applicable)
    cloud_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Artifact management
    max_artifact_size_mb: int = 100
    artifact_retention_days: Optional[int] = None


# ============================================================================
# SEARCH CONFIGURATION
# ============================================================================

class SearchBackendType(str, Enum):
    """Types of search backends."""
    SERPAPI = "serpapi"
    GOOGLE = "google"
    BING = "bing"
    DUCKDUCKGO = "duckduckgo"


class SearchConfig(BaseModel):
    """Configuration for search system."""
    enabled: bool = True
    backend: SearchBackendType = SearchBackendType.SERPAPI
    
    # API configuration
    api_key: Optional[str] = None
    max_results: int = 10
    timeout: int = 30
    
    # Search behavior
    safe_search: bool = True
    result_language: str = "en"
    
    # Backend-specific settings
    backend_config: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# ORCHESTRATOR CONFIGURATION
# ============================================================================

class OrchestratorConfig(BaseModel):
    """Configuration for task orchestrator."""
    # Routing brain (for multi-agent coordination)
    brain_config: Optional[BrainConfig] = None
    
    # Execution limits
    max_rounds: int = 50
    timeout: int = 3600  # seconds
    
    # Agent selection strategy
    routing_strategy: str = "intelligent"  # "intelligent", "round_robin", "random"
    
    # Coordination settings
    enable_agent_handoff: bool = True
    require_explicit_handoff: bool = False
    
    # Termination conditions
    auto_terminate: bool = True
    termination_keywords: List[str] = Field(default_factory=lambda: ["DONE", "COMPLETE", "FINISHED"])


# ============================================================================
# TOOL CONFIGURATION
# ============================================================================

class ToolConfig(BaseModel):
    """Configuration for individual tools."""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = None
    retry_policy: Dict[str, Any] = Field(default_factory=dict)


class ToolsConfig(BaseModel):
    """Configuration for the tool system."""
    # Built-in tools
    builtin_tools: List[str] = Field(default_factory=list)
    
    # Custom tool configurations
    tools: List[ToolConfig] = Field(default_factory=list)
    
    # Global tool settings
    execution_timeout: int = 300
    max_parallel_executions: int = 5
    enable_logging: bool = True
    
    # Security settings
    sandbox_enabled: bool = True
    allowed_operations: List[str] = Field(default_factory=list)


# ============================================================================
# TASK CONFIGURATION
# ============================================================================

class TaskConfig(BaseModel):
    """Configuration for task execution."""
    task_id: Optional[str] = None
    workspace_dir: Optional[str] = None
    
    # Execution settings
    max_execution_time: int = 7200  # 2 hours
    checkpoint_interval: int = 300  # 5 minutes
    
    # Logging and monitoring
    log_level: str = "INFO"
    enable_monitoring: bool = True
    
    # Task metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# TEAM CONFIGURATION (MAIN CONFIG)
# ============================================================================

class TeamConfig(BaseModel):
    """Main configuration for agent teams."""
    # Team metadata
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Agents configuration
    agents: List[Dict[str, Any]]  # Raw agent data, converted to AgentConfig later
    
    # System configurations
    orchestrator: Optional[OrchestratorConfig] = None
    memory: Optional[Union[MemoryConfig, Dict[str, Any]]] = None
    storage: Optional[StorageConfig] = None
    search: Optional[SearchConfig] = None
    tools: Optional[ToolsConfig] = None
    task: Optional[TaskConfig] = None
    
    # Global settings
    workspace_dir: Optional[str] = None
    config_dir: Optional[Path] = None
    
    # Environment settings
    environment: str = "development"  # "development", "staging", "production"
    debug: bool = False
    
    @validator('agents')
    def validate_agents(cls, v):
        """Ensure at least one agent is configured."""
        if not v:
            raise ValueError("At least one agent must be configured")
        return v
    
    def get_agent_names(self) -> List[str]:
        """Get list of agent names."""
        return [agent.get('name', f'agent_{i}') for i, agent in enumerate(self.agents)]
    
    def get_agent_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific agent."""
        for agent in self.agents:
            if agent.get('name') == name:
                return agent
        return None


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_team_config(config: TeamConfig) -> List[str]:
    """
    Validate team configuration and return list of validation errors.
    
    Args:
        config: Team configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Validate agent names are unique
    agent_names = config.get_agent_names()
    if len(agent_names) != len(set(agent_names)):
        errors.append("Agent names must be unique")
    
    # Validate each agent has required fields
    for i, agent in enumerate(config.agents):
        if not agent.get('name'):
            errors.append(f"Agent {i} missing required 'name' field")
        
        # Check for either system_message or prompt_file
        if not agent.get('system_message') and not agent.get('prompt_file'):
            errors.append(f"Agent '{agent.get('name', i)}' must have either 'system_message' or 'prompt_file'")
    
    # Validate memory configuration if present
    if config.memory and isinstance(config.memory, dict):
        if config.memory.get('enabled') and not config.memory.get('backend'):
            errors.append("Memory backend must be specified when memory is enabled")
    
    return errors


# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================

def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries, with override taking precedence.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration dictionary
    """
    merged = base_config.copy()
    
    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged


def get_default_team_config() -> TeamConfig:
    """Get a default team configuration for testing/examples."""
    return TeamConfig(
        name="default_team",
        description="Default team configuration",
        agents=[
            {
                "name": "assistant",
                "system_message": "You are a helpful AI assistant.",
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            }
        ]
    ) 