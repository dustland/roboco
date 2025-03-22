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
from roboco.agents.robotics_scientist import RoboticsScientist
from roboco.agents.genesis_agent import GenesisAgent
from roboco.agents.project_builder import ProjectBuilder
from roboco.agents.human_proxy import HumanProxy
# Import the base classes for convenience
from roboco.core.agent import Agent

__all__ = [
    'Agent',             # Base class for creating custom agents
    'GenesisAgent',      # Genesis agent
    'ProjectBuilder',    # Project builder agent
    'RoboticsScientist', # Robotics scientist agent
    'HumanProxy',        # Human proxy agent
]