# Roboco Logging Standards

This document outlines the standardized logging approach for the Roboco project.

## Core Principles

1. **Consistency**: All modules should use the same logging approach
2. **Context**: Logs should include module context to aid debugging
3. **Configuration**: Logging levels and formats should be configurable in a central place

## How to Use Logging in Roboco

### Step 1: Import the logger

Always import `get_logger` from the core logger module:

```python
from roboco.core.logger import get_logger
```

### Step 2: Initialize the logger with your module name

At the module level, create a logger instance with your module name:

```python
# Initialize logger
logger = get_logger(__name__)
```

### Step 3: Use the logger in your code

Use the appropriate logging methods based on severity:

```python
# Informational messages
logger.info("Operation completed successfully")

# Debug messages (won't show in production by default)
logger.debug("Processing item: {}", item_id)

# Warning messages
logger.warning("Resource usage is high: {}", usage_percent)

# Error messages
logger.error("Failed to process request: {}", str(e))

# Critical errors
logger.critical("System cannot continue: {}", error_message)
```

## Class-specific Loggers

For classes that need their own dedicated logger instance:

```python
class MyTool:
    def __init__(self):
        # Create a class-specific logger
        self.logger = get_logger(__name__)

    def some_method(self):
        self.logger.info("Method called")
```

## Benefits

1. **Consistent Output**: All logs follow the same format
2. **Module Context**: Logs are tagged with the source module name
3. **Centralized Configuration**: Logging behavior can be changed project-wide
4. **Flexible Formatting**: Log formats are standardized but customizable

## Migration Guide

When updating existing code:

1. Replace `from loguru import logger` with `from roboco.core.logger import get_logger`
2. Add `logger = get_logger(__name__)` after imports
3. Keep existing logger method calls (`logger.info()`, etc.) as they are
