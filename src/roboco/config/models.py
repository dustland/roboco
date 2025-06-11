"""
Configuration Models

Data models for Roboco configuration files, focusing on team collaboration
rather than rigid workflows.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

class TeamConfig(BaseModel):
    """Configuration for a collaborative team of agents."""
    name: str
    description: Optional[str] = None
    agents: List[str]  # Agent names/IDs in the team
    collaboration_settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AgentConfig(BaseModel):
    """Configuration for a collaborative agent."""
    name: str
    role: str
    model: str = "gpt-4"
    
    # Collaboration-specific settings
    collaboration_style: str = "cooperative"  # e.g., "cooperative", "competitive", "supportive"
    
    # Agent-specific details for collaboration
    collaboration_details: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ToolParameterConfig(BaseModel):
    """Configuration for a tool parameter."""
    name: str
    type: str  # JSON Schema type
    description: str
    required: bool = True
    default: Optional[Any] = None

class ToolConfig(BaseModel):
    """Configuration for a single tool."""
    name: str
    description: Optional[str] = None
    # Module path for the tool class (e.g., "roboco.builtin_tools.search_tools")
    module: str
    # Class name for the tool (e.g., "WebSearchTool")  
    class_name: str
    # Parameters to pass to tool constructor
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    # Tool parameter schema for validation
    parameters_schema: Optional[List[ToolParameterConfig]] = Field(default_factory=list)
    # Authorization settings
    allowed_agents: Optional[List[str]] = None
    # Rate limiting settings
    rate_limit: Optional[Dict[str, Any]] = None

@dataclass
class MemoryConfig:
    """Configuration for memory system using Mem0."""
    
    # Vector store configuration
    vector_store: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "provider": "qdrant",
        "config": {
            "collection_name": "roboco_memories",
            "host": "localhost",
            "port": 6333,
        }
    })
    
    # LLM configuration for memory extraction
    llm: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "provider": "openai",
        "config": {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 2048,
        }
    })
    
    # Embedder configuration
    embedder: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small"
        }
    })
    
    # Graph store configuration (optional)
    graph_store: Optional[Dict[str, Any]] = None
    
    # Memory version
    version: str = "v1.1"
    
    # Custom extraction prompt
    custom_fact_extraction_prompt: Optional[str] = None
    
    # History database path
    history_db_path: Optional[str] = None

class EventConfig(BaseModel):
    """Configuration for event system."""
    bus_type: str = "memory"  # Type of event bus
    persistence: bool = False
    config: Dict[str, Any] = Field(default_factory=dict)

class RobocoConfig(BaseModel):
    """Root configuration for a Roboco application."""
    version: str = "0.1.0"
    teams: Optional[List[TeamConfig]] = Field(default_factory=list)
    tools: Optional[List[ToolConfig]] = Field(default_factory=list)
    memory: Optional[MemoryConfig] = None
    events: Optional[EventConfig] = None
    # Global settings like logging, event bus config, context store config
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)
