"""
Logger Configuration Module

This module provides standard logger configuration for the roboco framework.
"""

import sys
import logging
from typing import Optional
from loguru import logger as loguru_logger


def setup_logger(
    level: str = "INFO",
    format_string: Optional[str] = None,
    sink = sys.stderr
):
    """
    Set up a standardized logger configuration for roboco.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string, if None will use default format
        sink: Where to output logs (default is stderr)
    
    Returns:
        Configured logger instance
    """
    # Remove any existing handlers
    loguru_logger.remove()
    
    # Default format if not specified
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    # Add the handler with the specified configuration
    loguru_logger.add(
        sink=sink,
        level=level.upper(),
        format=format_string,
        colorize=True,
    )
    
    return loguru_logger


def get_logger(name: Optional[str] = None):
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name, typically the module name
        
    Returns:
        Logger instance with the requested name
    """
    if name:
        return loguru_logger.bind(name=name)
    return loguru_logger


# Set up the default logger
setup_logger() 