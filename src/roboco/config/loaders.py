from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

import yaml
from pydantic import ValidationError

from .models import RobocoConfig
from roboco.core.exceptions import ConfigurationError

class ConfigLoader(ABC):
    """
    Abstract base class for configuration loaders.
    Defines the interface for loading Roboco configurations.
    """

    @abstractmethod
    def load_config(self, source: Any, **kwargs: Any) -> RobocoConfig:
        """
        Load configuration from a given source.

        Args:
            source: The source of the configuration (e.g., file path, dict).
            **kwargs: Additional arguments specific to the loader implementation.

        Returns:
            A RobocoConfig object.

        Raises:
            ConfigurationError: If there's an error loading or validating the config.
        """
        pass

    def load_config_from_file(self, file_path: str, **kwargs: Any) -> RobocoConfig:
        """
        Helper method to load configuration from a file path.
        Subclasses can override this if they primarily deal with files.
        By default, it raises NotImplementedError if the main load_config
        doesn't handle file paths directly.
        """
        # Default implementation assumes load_config can handle file_path as source
        # or that subclasses specializing in file loading will override this.
        return self.load_config(source=file_path, **kwargs)

    def load_config_from_dict(self, config_dict: Dict[str, Any], **kwargs: Any) -> RobocoConfig:
        """
        Helper method to load configuration from a dictionary.
        Subclasses can override this.
        """
        # Default implementation assumes load_config can handle dict as source
        return self.load_config(source=config_dict, **kwargs)

class YamlConfigLoader(ConfigLoader):
    """Loads Roboco configuration from a YAML file."""

    def load_config(self, source: Any, **kwargs: Any) -> RobocoConfig:
        """
        Load configuration from a YAML file path.

        Args:
            source: The file path (string) to the YAML configuration file.
            **kwargs: Additional arguments (not used by this loader).

        Returns:
            A RobocoConfig object.

        Raises:
            ConfigurationError: If the source is not a string, the file is not found,
                                the YAML is invalid, or validation against RobocoConfig fails.
        """
        if not isinstance(source, str):
            raise ConfigurationError("YAML source must be a file path (string).")
        
        file_path = source
        try:
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            if not isinstance(config_data, dict):
                raise ConfigurationError(f"Invalid YAML format in {file_path}. Expected a dictionary, got {type(config_data)}.")
            
            return RobocoConfig(**config_data)
        except FileNotFoundError:
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML file {file_path}: {e}")
        except ValidationError as e:
            # Provide more detailed Pydantic validation errors
            error_details = e.errors()
            raise ConfigurationError(f"Configuration validation error for {file_path}: {error_details}")
        except Exception as e:
            # Catch any other unexpected errors during loading or parsing
            raise ConfigurationError(f"Unexpected error loading configuration from {file_path}: {e}")

    def load_config_from_file(self, file_path: str, **kwargs: Any) -> RobocoConfig:
        """
        Helper method to load configuration from a file path.
        This directly calls load_config for YAML files.
        """
        return self.load_config(source=file_path, **kwargs)
