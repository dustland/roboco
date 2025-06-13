"""
Roboco - Multi-Agent Collaboration Framework

A framework for multi-agent collaboration where users can control, monitor, 
and interact with teams of AI agents working together on tasks.

Core Workflow:
    1. Configure team (agents + tools) → team.yaml
    2. Create and start collaborative task
    3. Monitor agent collaboration in real-time  
    4. Access chat and memory interfaces
    5. Fetch results and manage task lifecycle

New Task-Centric API:

# Task Management
from roboco import create_task, get_task, list_tasks

task = create_task("team.yaml")  # Create but don't start
task = get_task(task_id)         # Get existing task
tasks = list_tasks()             # All tasks

# Task Lifecycle
await task.start("description")  # Smart start/resume
await task.stop()               # Stop collaboration
await task.delete()             # Clean up

# Event Handling
task.on("event", handler)
task.off("event", handler)

# Chat Session Access
session = task.get_chat()
history = session.get_chat_history()
await session.send_message("message")

# Memory Operations (Mem0-aligned)
memory = task.get_memory()
memory.add(messages, agent_id="planner")
memory.search("keyword", agent_id="planner")
memory.get_all(agent_id="researcher")
"""

# Task Management API
from .core.task import create_task, get_task, list_tasks, Task, TaskInfo, ChatSession, TaskMemory

# Core types for advanced usage
from .core.models import TaskResult
from .core.exceptions import ConfigurationError

# Version info
__version__ = "0.8.0"

# Clean Task-Centric API
__all__ = [
    # Task Management
    "create_task",     # Create new task
    "get_task",        # Get existing task
    "list_tasks",      # List all tasks
    
    # Core Classes
    "Task",            # Main task class
    "TaskInfo",        # Task information
    "ChatSession",     # Chat interface
    "TaskMemory",      # Memory interface
    
    # Result types
    "TaskResult",
    "ConfigurationError",
    
    # Package info
    "__version__",
]
