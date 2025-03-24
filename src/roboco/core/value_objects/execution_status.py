"""
Execution status value objects.
"""
from enum import Enum


class ExecutionStatus(str, Enum):
    """Status of execution."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
