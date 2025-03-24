"""
Phase status value objects.
"""
from enum import Enum


class PhaseStatus(str, Enum):
    """Status of a phase."""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"
