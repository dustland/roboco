"""Logging configuration for RoboCo."""

import sys
from pathlib import Path
from loguru import logger

def setup_logging(
    log_file: str = "roboco.log",
    log_level: str = "INFO",
    rotation: str = "500 MB",
    retention: str = "10 days"
) -> None:
    """Configure logging for the application.
    
    Args:
        log_file: Name of the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: When to rotate the log file
        retention: How long to keep log files
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler with colored output
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )
    
    # Add file handler
    logger.add(
        log_dir / log_file,
        rotation=rotation,
        retention=retention,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    
    logger.info(f"Logging configured with level {log_level}") 