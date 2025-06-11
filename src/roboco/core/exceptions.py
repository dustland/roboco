class RobocoException(Exception):
    """Base exception class for all Roboco errors."""
    pass

class ConfigurationError(RobocoException):
    """Raised for errors in configuration."""
    pass

class InitializationError(RobocoException):
    """Raised for errors during component initialization."""
    pass

class ToolExecutionError(RobocoException):
    """Raised for errors during tool execution."""
    pass

class AgentError(RobocoException):
    """Raised for errors related to agent operations."""
    pass

class ContextError(RobocoException):
    """Raised for errors within the context management system."""
    pass

class EventError(RobocoException):
    """Raised for errors within the event system."""
    pass
