"""
Task schema definitions.
"""
from enum import Enum


class TaskStatus(str, Enum):
    """Status of a task."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
