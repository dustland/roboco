from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncGenerator

class Runnable(ABC):
    """
    Interface for components that can be run, often asynchronously,
    processing input and producing output.
    """

    @abstractmethod
    async def run(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute the runnable component.

        Args:
            input_data: The primary input for the component.
            config: Optional configuration specific to this run.

        Returns:
            The output of the component's execution.
        """
        pass

class Streamable(ABC):
    """
    Interface for components that can stream their output.
    """
    @abstractmethod
    async def stream(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> AsyncGenerator[Any, None]:
        """
        Stream the output of the component.

        Args:
            input_data: The primary input for the component.
            config: Optional configuration specific to this run.

        Yields:
            Chunks of the component's output.
        """
        # Ensure the generator is properly defined even if not implemented initially
        if False: # pragma: no cover
            yield

class Initializable(ABC):
    """
    Interface for components that require initialization, typically with configuration.
    """
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize the component with the given configuration.

        Args:
            config: Configuration parameters for the component.
        """
        pass

class Configurable(ABC):
    """
    Interface for components that can provide their default configuration schema.
    """
    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> Dict[str, Any]:
        """
        Returns the JSON schema for the component's configuration.
        This can be used for validation and UI generation.
        """
        pass
