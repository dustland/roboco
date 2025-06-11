from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, AsyncGenerator

# Using ToolParameterConfig from config.models for schema definition consistency
from roboco.config.models import ToolParameterConfig
from roboco.core.interfaces import Runnable, Streamable, Configurable

class AbstractTool(Runnable, Streamable, Configurable, ABC):
    """
    Abstract base class for all tools in the Roboco system.
    A tool is a component that performs a specific task, often an external action
    or computation, and can be invoked by agents.

    It inherits from:
    - Runnable: For `async def run()` execution.
    - Streamable: For `async def stream()` for tools that support streaming output.
    - Configurable: For `classmethod def get_config_schema()` to define its own configuration needs
      beyond invocation parameters (e.g., API keys, default settings).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The unique name of the tool.
        This should match the name used in configuration and for invocation.
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        A human-readable description of what the tool does.
        """
        pass

    @abstractmethod
    def get_invocation_schema(self) -> List[ToolParameterConfig]:
        """
        Returns the schema for the parameters required to invoke this tool.
        This schema defines the inputs the tool expects for its `run` or `stream` methods.
        It should be a list of ToolParameterConfig objects.
        """
        pass

    # The `run` and `stream` methods are inherited from Runnable and Streamable.
    # The `input_data` for these methods will typically be a dictionary
    # conforming to the schema returned by `get_invocation_schema()`.
    # The `config` parameter in `run` can be used for run-specific overrides
    # of the tool's own configuration or for passing other contextual information.

    # The `get_config_schema` method is inherited from Configurable.
    # This schema defines the tool's own persistent configuration,
    # distinct from the parameters it takes for each invocation.
    # For example, an API key or a default model for an AI tool.
