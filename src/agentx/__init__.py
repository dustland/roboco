"""
AgentX - Multi-Agent Collaboration Framework

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
from agentx import create_task, get_task, list_tasks

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

# Memory Operations (via agents)
# Each agent has its own elegant Memory instance
agent.save_memory("content")
agent.search_memory("query")
"""

# Task Management API - TODO: Implement these modules
# from .core.task import create_task, get_task, list_tasks, Task, TaskInfo, ChatSession

# Core types for advanced usage
# from .core.exceptions import ConfigurationError

# Version info
__version__ = "0.8.0"

def initialize():
    """
    Initialize the AgentX framework.
    
    This should be called once at application startup to:
    - Register built-in tools
    - Initialize event system
    - Set up logging
    """
    from .tools import register_builtin_tools
    register_builtin_tools()

# Clean Task-Centric API
__all__ = [
    # Package info
    "__version__",
    "initialize",
]
