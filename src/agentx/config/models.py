"""
Configuration Models

Data models for AgentX configuration files, focusing on team collaboration
and matching the design document structure.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from dataclasses import dataclass, field

# Note: AgentConfig is imported in __init__.py to avoid circular imports

class LLMProviderConfig(BaseModel):
    """LLM provider configuration."""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None

@dataclass
class MemoryConfig:
    """Configuration for memory system using Mem0."""
    
    # Vector store configuration
    vector_store: Optional[Dict[str, Any]] = field(default_factory=lambda: {
        "provider": "qdrant",
        "config": {
            "collection_name": "agentx_memories",
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

class TeamConfig(BaseModel):
    """
    Team configuration matching the design document structure.
    This represents a complete team.yaml file.
    """
    name: str
    description: Optional[str] = None
    
    # LLM provider settings (can be in .env instead)
    llm_provider: Optional[LLMProviderConfig] = None
    
    # List of agent configurations (full configs, not just names)
    agents: List[Dict[str, Any]]  # Raw agent data from YAML
    
    # Team collaboration controls (merged from CollaborationConfig)
    speaker_selection_method: str = "auto"  # auto, round_robin, manual
    max_rounds: int = 10
    termination_condition: str = "TERMINATE"
    timeout_minutes: Optional[int] = None
    auto_terminate_keywords: Optional[List[str]] = None
    speaker_order: Optional[List[str]] = None
    
    # Tool configurations (flexible dict for now)
    tools: Optional[Dict[str, Any]] = None
    
    # Memory configuration
    memory: Optional[MemoryConfig] = None
