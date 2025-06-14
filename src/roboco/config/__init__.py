"""
Configuration system for Roboco.

Public API:
- load_team_config: Load team configuration from YAML files
- validate_team_config: Validate team configuration
- MemoryConfig: Memory system configuration (used by memory backends)
- TeamConfig, LLMProviderConfig: Core config models
"""

from .models import (
    TeamConfig,
    LLMProviderConfig,
    MemoryConfig,
)
from .team_loader import (
    load_team_config,
    validate_team_config
)

# Note: AgentConfig imported in individual modules to avoid circular imports

__all__ = [
    # Main API (matching design document)
    "load_team_config",
    "validate_team_config",
    
    # Core config models used by other modules
    "TeamConfig",
    "LLMProviderConfig", 
    "MemoryConfig",
]
