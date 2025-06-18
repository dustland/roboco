"""
Logging utilities for AgentX.
"""

import logging
import sys
import warnings
from typing import Optional
import os


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Set level based on environment or default
        log_level = level or _get_default_log_level()
        logger.setLevel(log_level)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    return logger


def configure_logging(level: str = "INFO", format_string: Optional[str] = None):
    """
    Configure global logging settings.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Optional custom format string
    """
    log_format = format_string or '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
    )


def setup_clean_chat_logging():
    """
    Configure logging for clean chat experience.
    Suppresses noisy logs unless verbose mode is enabled.
    """
    verbose = _is_verbose_mode()
    
    if verbose:
        configure_logging(level="INFO")
    else:
        # Clean chat mode - only show warnings and errors
        configure_logging(level="WARNING")
        
        # Suppress specific noisy loggers
        logging.getLogger("LiteLLM").setLevel(logging.ERROR)
        logging.getLogger("browser_use.telemetry.service").setLevel(logging.ERROR)
        logging.getLogger("agentx.storage").setLevel(logging.ERROR)
        logging.getLogger("agentx.builtin_tools").setLevel(logging.ERROR)
        logging.getLogger("agentx.memory").setLevel(logging.ERROR)
        
        # Suppress Pydantic warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def _get_default_log_level() -> str:
    """Get default log level based on environment."""
    if _is_verbose_mode():
        return "INFO"
    else:
        return "WARNING"


def _is_verbose_mode() -> bool:
    """Check if verbose mode is enabled via environment variable."""
    return os.getenv("AGENTX_VERBOSE", "").lower() in ("1", "true", "yes") 