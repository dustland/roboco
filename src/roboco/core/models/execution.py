"""
Execution model definitions.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from roboco.core.value_objects.execution_status import ExecutionStatus


class ExecutionResult(BaseModel):
    """Represents the result of a task execution."""
    task_id: str
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float
    artifacts: Dict[str, Any] = Field(default_factory=dict)


class PhaseResult(BaseModel):
    """Represents the result of a phase execution."""
    name: str
    tasks: List[Dict[str, Any]]
    success: bool
    execution_time: float


class ExecutionState(BaseModel):
    """Tracks the current execution state for UI display."""
    current_phase: Optional[str] = None
    current_task: Optional[str] = None
    status: ExecutionStatus = ExecutionStatus.IDLE
    progress: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
