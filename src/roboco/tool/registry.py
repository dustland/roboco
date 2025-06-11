from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Type # Type is kept for now, though not actively used by current ABC
import importlib

from .interfaces import AbstractTool
from roboco.config.models import ToolConfig
from roboco.core.exceptions import ConfigurationError, ToolExecutionError

class AbstractToolRegistry(ABC):
    """
    Abstract base class for a tool registry.
    The registry is responsible for discovering, storing, and providing access
    to tool instances or their configurations.
    """

    @abstractmethod
    async def register_tool(self, tool: AbstractTool) -> None:
        """
        Register an already instantiated tool object.

        Args:
            tool: An instance of a class derived from AbstractTool.
        """
        pass

    @abstractmethod
    async def register_tool_from_config(self, tool_config: ToolConfig) -> None:
        """
        Register and potentially instantiate a tool based on its configuration.
        The registry might decide to lazy-load/instantiate tools.

        Args:
            tool_config: A ToolConfig object describing the tool.
        """
        pass

    @abstractmethod
    async def get_tool(self, tool_name: str) -> Optional[AbstractTool]:
        """
        Retrieve an instantiated tool by its name.

        Args:
            tool_name: The name of the tool to retrieve.

        Returns:
            An instance of the tool if found and instantiated, otherwise None.
        """
        pass

    @abstractmethod
    async def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        """
        Retrieve the configuration for a tool by its name.
        This is useful if the tool itself is not yet instantiated or if only
        config details are needed.

        Args:
            tool_name: The name of the tool.

        Returns:
            The ToolConfig object if the tool is registered, otherwise None.
        """
        pass

    @abstractmethod
    async def list_tools(self) -> List[AbstractTool]:
        """
        List all available (instantiated) tools.

        Returns:
            A list of AbstractTool instances.
        """
        pass

    @abstractmethod
    async def list_tool_configs(self) -> List[ToolConfig]:
        """
        List configurations of all registered tools.

        Returns:
            A list of ToolConfig objects.
        """
        pass

    @abstractmethod
    async def unregister_tool(self, tool_name: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            tool_name: The name of the tool to unregister.

        Returns:
            True if the tool was found and removed, False otherwise.
        """
        pass

    @abstractmethod
    async def load_tools_from_configs(self, tool_configs: List[ToolConfig]) -> None:
        """
        Load and register multiple tools from a list of configurations.

        Args:
            tool_configs: A list of ToolConfig objects.
        """
        pass


class InMemoryToolRegistry(AbstractToolRegistry):
    """
    An in-memory implementation of the AbstractToolRegistry.
    Stores tools and their configurations in memory.
    Dynamically instantiates tools from configuration.
    """

    def __init__(self):
        self._tools: Dict[str, AbstractTool] = {}
        self._tool_configs: Dict[str, ToolConfig] = {}

    def _instantiate_tool_from_config(self, tool_config: ToolConfig) -> AbstractTool:
        """
        Helper method to dynamically import and instantiate a tool from its configuration.
        """
        try:
            module_path = tool_config.module
            class_name = tool_config.class_name

            if not module_path or not class_name:
                raise ConfigurationError(
                    f"Tool '{tool_config.name}' configuration is missing 'module' or 'class_name'."
                )

            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)

            if not issubclass(tool_class, AbstractTool):
                raise ConfigurationError(
                    f"Class {module_path}.{class_name} for tool '{tool_config.name}' "
                    f"does not inherit from AbstractTool."
                )
            
            tool_instance = tool_class(**(tool_config.parameters or {}))
            
            if not tool_instance.name:
                raise ConfigurationError(
                    f"Tool instance of {module_path}.{class_name} for config '{tool_config.name}' "
                    f"did not set its 'name' property upon initialization."
                )
            return tool_instance

        except ImportError as e:
            raise ConfigurationError(
                f"Failed to import module '{module_path}' for tool '{tool_config.name}': {e}"
            )
        except AttributeError as e:
            raise ConfigurationError(
                f"Failed to find class '{class_name}' in module '{module_path}' "
                f"for tool '{tool_config.name}': {e}"
            )
        except Exception as e:
            raise ToolExecutionError(
                f"Failed to instantiate tool '{tool_config.name}' from class "
                f"{module_path}.{class_name}: {e}"
            )

    async def register_tool(self, tool: AbstractTool, overwrite: bool = False) -> None:
        if not tool.name:
            raise ValueError("Tool name cannot be empty for registration.")
        
        if tool.name in self._tools and not overwrite:
            raise ValueError(
                f"Tool with name '{tool.name}' is already registered. Set overwrite=True to replace."
            )
        self._tools[tool.name] = tool

    async def register_tool_from_config(self, tool_config: ToolConfig, overwrite: bool = False) -> None:
        if not tool_config.name:
            raise ValueError("ToolConfig 'name' cannot be empty for registration.")

        if tool_config.name in self._tool_configs and not overwrite:
            raise ValueError(
                f"Tool configuration for '{tool_config.name}' is already registered. "
                f"Set overwrite=True to replace."
            )
        
        tool_instance = self._instantiate_tool_from_config(tool_config)
        
        registration_name = tool_config.name 

        if registration_name in self._tools and not overwrite:
             raise ValueError(
                f"A tool (possibly from direct registration) with name '{registration_name}' "
                f"is already registered. Set overwrite=True to replace."
            )

        self._tools[registration_name] = tool_instance
        self._tool_configs[registration_name] = tool_config

    async def get_tool(self, tool_name: str) -> Optional[AbstractTool]:
        return self._tools.get(tool_name)

    async def get_tool_config(self, tool_name: str) -> Optional[ToolConfig]:
        return self._tool_configs.get(tool_name)

    async def list_tools(self) -> List[AbstractTool]:
        return list(self._tools.values())

    async def list_tool_configs(self) -> List[ToolConfig]:
        return list(self._tool_configs.values())

    async def unregister_tool(self, tool_name: str) -> bool:
        tool_existed = tool_name in self._tools
        config_existed = tool_name in self._tool_configs
        
        if tool_existed:
            del self._tools[tool_name]
        if config_existed:
            del self._tool_configs[tool_name]
            
        return tool_existed or config_existed

    async def load_tools_from_configs(self, tool_configs: List[ToolConfig], overwrite: bool = False) -> None:
        for config in tool_configs:
            try:
                await self.register_tool_from_config(config, overwrite=overwrite)
            except (ConfigurationError, ToolExecutionError, ValueError) as e:
                print(f"Skipping registration of tool '{config.name}' due to error: {e}")
