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

Minimal Usage:
    from agentx import start_task
    task = start_task("hi")
    while not task.is_complete:
        await task.step()
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
    # Suppress verbose logs and warnings
    import logging
    import warnings
    
    # Suppress LiteLLM verbose logging
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    
    # Suppress Pydantic serialization warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
    
    # Set litellm to non-verbose mode
    try:
        import litellm
        litellm.set_verbose = False
    except ImportError:
        pass
    
    from .tools import register_builtin_tools
    register_builtin_tools()

def execute_task(prompt: str, config_path: str, stream: bool = False):
    """
    Execute a task to completion (one-shot execution).
    
    Args:
        prompt: Task prompt/message
        config_path: Path to team configuration file
        stream: Whether to stream responses
    
    Returns:
        Async generator yielding execution updates if stream=True,
        otherwise returns final result
    """
    initialize()
    
    from .core.task import create_task
    task = create_task(config_path)
    return task.execute_task(prompt, stream=stream)

def start_task(prompt: str, config_path: str = None):
    """
    Start a task with minimal setup.
    
    Args:
        prompt: Initial prompt/message
        config_path: Optional team config path (creates default if not provided)
    
    Returns:
        Task instance ready for step() calls
    """
    initialize()
    
    if config_path:
        from .core import create_task
        task = create_task(config_path)
        task.start_task(prompt)
        return task
    else:
        # Create minimal default task
        from .core.agent import Agent
        from .core.config import AgentConfig, LLMConfig, TeamConfig
        from .core.team import Team
        from .core.task import Task
        from pathlib import Path
        import tempfile
        import os
        
        # Create a temporary directory for the template
        temp_dir = Path(tempfile.mkdtemp())
        template_file = temp_dir / "assistant_prompt.txt"
        
        # Write the template content
        template_content = "You are a helpful AI assistant. Respond to the user's message."
        with open(template_file, 'w') as f:
            f.write(template_content)
        
        agent_config = AgentConfig(
            name="assistant",
            description="AI assistant",
            prompt_template="assistant_prompt.txt",
            llm_config=LLMConfig(model="deepseek-chat")
        )
        
        team_config = TeamConfig(
            name="Chat",
            description="Simple chat team",
            agents=[agent_config]
        )
        
        team = Team(team_config, temp_dir)
        task = Task(team, workspace_dir=temp_dir)
        task.start_task(prompt)
        return task

# Clean Task-Centric API
__all__ = [
    # Package info
    "__version__",
    "initialize",
    "start_task",
    "execute_task",
]
