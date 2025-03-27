#!/usr/bin/env python3
"""
Application Entry Point Example

This example demonstrates how to properly initialize the logging system
and avoid circular import issues.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path if needed
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Initialize logging with default settings first
from loguru import logger
logger.info("Application starting...")

# Import core modules
from roboco.core.config import load_config
from roboco.core.logger import configure_logger, load_config_settings

# After all core modules are imported, configure logging from config
logger.info("Loading configuration...")
config = load_config()
load_config_settings()  # Now it's safe to load config because all imports are resolved

logger.info("Configuration loaded, log level set from config")

# Now import and use other modules that depend on logging
from roboco.core.task_manager import TaskManager

def main():
    """Main application entry point"""
    logger.info("Initializing application components...")
    
    # Example logging at different levels
    logger.debug("This is a debug message - only shown if log_level is DEBUG")
    logger.info("Application initialization complete")
    logger.warning("This is a sample warning")
    
    # Create a structured log
    logger.info({
        "event": "app_started",
        "version": "1.0.0",
        "env": os.environ.get("ENVIRONMENT", "development")
    })
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        logger.info(f"Application exited with code {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        sys.exit(1) 