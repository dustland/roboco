"""
Custom Agent Classes

This module provides a base for creating custom Agent subclasses with specialized behavior.
Most standard agents have been migrated to the configuration-based system with
prompts defined in markdown files in the config/prompts/ directory.

For most use cases, using role markdown files and the configuration-based team system
is recommended. However, creating custom Agent subclasses remains fully supported
for specialized needs that can't be expressed through configuration alone.
"""
# Import the remaining specialized agent
from roboco.agents.genesis_agent import GenesisAgent
from roboco.agents.planner import Planner
from roboco.agents.human_proxy import HumanProxy

__all__ = [
    'GenesisAgent',      # Genesis agent
    'Planner',           # Project planner agent
    'HumanProxy',        # Human proxy agent
]