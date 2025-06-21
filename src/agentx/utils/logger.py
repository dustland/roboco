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
        _suppress_noisy_loggers()
        
        # Suppress Pydantic warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")


def set_log_level(level: str):
    """
    Set log level for the entire application.
    
    This is the main function to control logging throughout AgentX.
    It intelligently handles different log levels:
    - DEBUG: Shows everything including external library logs
    - INFO: Shows AgentX logs but suppresses noisy external libraries  
    - WARNING: Shows only warnings and errors, suppresses most noise
    - ERROR: Shows only errors and critical issues
    - CRITICAL: Shows only critical errors
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Force AgentX verbose mode off initially
    os.environ['AGENTX_VERBOSE'] = '0'
    
    level_upper = level.upper()
    log_level = getattr(logging, level_upper)
    
    # Configure root logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s' if level_upper in ['DEBUG', 'INFO'] else '%(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout,
        force=True  # Override existing configuration
    )
    
    if level_upper == 'DEBUG':
        # DEBUG: Show everything, including external libraries
        logging.getLogger().setLevel(logging.DEBUG)
        # Don't suppress anything in debug mode
        
    elif level_upper == 'INFO':
        # INFO: Show AgentX logs, suppress noisy external libraries
        logging.getLogger().setLevel(logging.INFO)
        _suppress_noisy_loggers(level="WARNING")
        
    elif level_upper == 'WARNING':
        # WARNING: Clean mode - only warnings and errors
        logging.getLogger().setLevel(logging.WARNING)
        _suppress_noisy_loggers(level="ERROR")
        _suppress_warnings()
        
    elif level_upper in ['ERROR', 'CRITICAL']:
        # ERROR/CRITICAL: Minimal logging
        logging.getLogger().setLevel(log_level)
        _suppress_noisy_loggers(level="CRITICAL")
        _suppress_warnings()


def _suppress_noisy_loggers(level: str = "ERROR"):
    """Suppress specific noisy loggers."""
    noisy_loggers = [
        "LiteLLM",
        "browser_use.telemetry.service", 
        "browser_use",
        "httpx",
        "urllib3.connectionpool",
        "urllib3",
        "requests.packages.urllib3",
        "selenium",
        "asyncio"
    ]
    
    log_level = getattr(logging, level.upper())
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(log_level)


def _suppress_warnings():
    """Suppress common warnings that clutter output."""
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
    warnings.filterwarnings("ignore", category=DeprecationWarning)


def _get_default_log_level() -> str:
    """Get default log level based on environment."""
    if _is_verbose_mode():
        return "INFO"
    else:
        return "WARNING"


def _is_verbose_mode() -> bool:
    """Check if verbose mode is enabled via environment variable."""
    return os.getenv("AGENTX_VERBOSE", "").lower() in ("1", "true", "yes") 