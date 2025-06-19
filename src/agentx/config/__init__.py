"""
Configuration system for AgentX.

Public API:
- load_team_config: Load team configuration from YAML files (if needed)
- MemoryConfig: Memory system configuration (used by memory backends)  
- TeamConfig, LLMProviderConfig: Core config models (if needed)

Recommended usage:
    from agentx import execute_task
    result = execute_task("config_dir", "Your task here")
"""

from .models import MemoryConfig, TeamConfig
from .team_loader import load_team_config

# Note: AgentConfig imported in individual modules to avoid circular imports

__all__ = [
    # Main API (for advanced usage - prefer Team.from_config())
    "load_team_config",
    
    # Core config models (for advanced usage)
    "TeamConfig",
    "MemoryConfig",
]
