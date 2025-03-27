"""
Logger Configuration Module

This module provides centralized logger configuration for the loguru logger used throughout the roboco framework.
It configures the loguru logger globally when imported.
"""

import sys
import os
from typing import Optional, Any, Dict, Union
from loguru import logger

# Store original logger configuration IDs for potential reset
_default_handler_ids = list(logger._core.handlers.keys())

# Flag to prevent circular imports when loading config
_config_loaded = False

def configure_logger(
    level: str = "INFO",
    format_string: Optional[str] = None,
    sink: Any = sys.stderr,
    **kwargs
) -> None:
    """
    Configure the global loguru logger.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string, if None will use default format
        sink: Where to output logs (default is stderr)
        **kwargs: Additional configuration parameters to pass to loguru.add()
    """
    # Remove any existing handlers
    logger.remove()
    
    # Default format if not specified
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    # Add the handler with the specified configuration
    logger.add(
        sink=sink,
        level=level.upper(),
        format=format_string,
        colorize=True,
        **kwargs
    )

def enable_file_logging(filepath: str, rotation: str = "10 MB", retention: str = "1 week", 
                       level: str = "DEBUG", **kwargs) -> int:
    """
    Enable logging to a file in addition to standard output.
    
    Args:
        filepath: Path to the log file
        rotation: When to rotate the log file (e.g., "10 MB", "1 day")
        retention: How long to keep log files (e.g., "1 week", "5 days")
        level: Log level for the file handler
        **kwargs: Additional configuration parameters
        
    Returns:
        Handler ID for the added file handler
    """
    return logger.add(
        sink=filepath,
        level=level.upper(),
        rotation=rotation,
        retention=retention,
        **kwargs
    )

def disable_file_logging(handler_id: int) -> None:
    """
    Disable file logging for a specific handler.
    
    Args:
        handler_id: Handler ID returned from enable_file_logging
    """
    logger.remove(handler_id)

def reset_logger() -> None:
    """
    Reset the logger to its default configuration.
    """
    # Remove all handlers
    logger.remove()
    
    # Re-initialize with default configuration 
    configure_logger()

def load_config_settings():
    """
    Load log level from config file.
    This should be called explicitly from the application entry point
    after all imports are resolved to prevent circular imports.
    """
    global _config_loaded
    if _config_loaded:
        return
        
    try:
        from roboco.core.config import load_config
        config = load_config()
        
        # Handle either a dictionary or RobocoConfig object
        if hasattr(config, "get") and callable(config.get):
            log_level = config.get("log_level", "INFO")
        elif hasattr(config, "log_level"):
            log_level = config.log_level
        else:
            log_level = "INFO"
            
        logger.info(f"Setting log level from config: {log_level}")
        configure_logger(level=log_level)
        _config_loaded = True
    except Exception as e:
        logger.warning(f"Could not load log level from config, using default: {e}")

# Initialize with default configuration only
# The load_config_settings() function should be called explicitly 
# from the application's entry point after all modules are imported
configure_logger() 