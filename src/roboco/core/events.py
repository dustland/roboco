"""
Task-specific events for the Roboco framework.

This module defines events that are emitted during task lifecycle operations.
These are high-level task events, while roboco.event contains the base Event 
infrastructure and general collaboration events.
"""

from ..event.events import Event
from typing import List


class TaskStartedEvent(Event):
    """Event emitted when a task starts."""
    def __init__(self, task_id: str, team_name: str, task_description: str, participants: List[str]):
        super().__init__(
            event_type="task.started",
            data={
                "task_id": task_id,
                "team_name": team_name,
                "task_description": task_description,
                "participants": participants
            }
        )


class TaskCompletedEvent(Event):
    """Event emitted when a task completes."""
    def __init__(self, task_id: str, team_name: str, task_description: str, participants: List[str], success: bool, summary: str):
        super().__init__(
            event_type="task.completed",
            data={
                "task_id": task_id,
                "team_name": team_name,
                "task_description": task_description,
                "participants": participants,
                "success": success,
                "summary": summary
            }
        )


class TaskStatusChangedEvent(Event):
    """Event emitted when a task status changes."""
    def __init__(self, task_id: str, old_status: str, new_status: str):
        super().__init__(
            event_type="task.status_changed",
            data={
                "task_id": task_id,
                "old_status": old_status,
                "new_status": new_status
            }
        )


class TaskCreatedEvent(Event):
    """Event emitted when a task is created."""
    def __init__(self, task_id: str, description: str, config_path: str):
        super().__init__(
            event_type="task.created",
            data={
                "task_id": task_id,
                "description": description,
                "config_path": config_path
            }
        )


class TaskDeletedEvent(Event):
    """Event emitted when a task is deleted."""
    def __init__(self, task_id: str):
        super().__init__(
            event_type="task.deleted",
            data={
                "task_id": task_id
            }
        ) 