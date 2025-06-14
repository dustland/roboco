"""
Roboco Core - An Opinionated Agent Framework

Built with freedom of extensibility and best-in-class integrations:
- SERP API for web search (built-in)
- Firecrawl for web content extraction (replaces Jina)
- browser-use for AI-first browser automation (better than Playwright)
- Mem0 for intelligent memory management
- Daytona for secure code execution (sub-90ms sandboxes)
- MCP (Model Context Protocol) for tool extensions
- OpenAI for LLM inference with function calling

Architecture: Task → Team → Agent → (Chat, Tool, Memory, Event)

This is an opinionated framework that makes the best choices by default
while providing complete freedom to extend and customize.
"""

# Core agent framework
from .agent import Agent, AgentRole, AgentConfig, create_assistant_agent, create_user_agent, create_code_agent
from .team import Team, TeamConfig, SpeakerSelectionMethod, create_team
from .brain import Brain, Message, ChatHistory, BrainConfig
from .tool import Tool, ToolRegistry, FunctionTool, CodeExecutionTool, register_tool, register_function
from .memory import Memory, MemoryItem
from .event import Event, EventBus, EventType, global_events

# High-level APIs (backwards compatibility)
from .task import Task, TaskConfig, TaskStatus

# Core types and exceptions

__version__ = "0.8.0"

__all__ = [
    # Core Framework (New Architecture)
    "Agent",
    "Team", 
    "Brain",
    "Tool",
    "Memory",
    "Event",
    
    # Agent Types & Config
    "AgentRole",
    "AgentConfig",
    "create_assistant_agent",
    "create_user_agent", 
    "create_code_agent",
    
    # Team Management
    "TeamConfig",
    "SpeakerSelectionMethod",
    "create_team",
    
    # Chat & Messaging
    "Message",
    "ChatHistory",
    
    # Tools & Functions
    "ToolRegistry",
    "FunctionTool",
    "CodeExecutionTool",
    "register_tool",
    "register_function",
    
    # Memory Management
    "MemoryItem",
    
    # Event System
    "EventBus",
    "EventType",
    "global_events",
    
    # High-Level APIs (Backwards Compatibility)
    "Task",
    "TaskConfig", 
    "TaskStatus",
    
    # Core Types & Exceptions
    "TaskResult",
    "RobocoException",
    "ConfigurationError", 
    "InitializationError",
    "ToolExecutionError",
    "AgentError",
    "EventError",
    
    # Interfaces
    "Runnable",
    "Streamable", 
    "Initializable",
    "Configurable",
]

# Opinionated defaults and integrations
BUILTIN_INTEGRATIONS = {
    "search": "serp",           # SERP API for web search
    "web_extraction": "firecrawl",  # Firecrawl for content extraction
    "browser_automation": "browser-use",  # AI-first browser automation
    "memory": "mem0",           # Mem0 for intelligent memory
    "execution": "daytona",     # Daytona for code execution
    "tools": "mcp",             # Model Context Protocol
    "llm": "openai",            # OpenAI for LLM inference
}

def get_integration_info() -> dict:
    """Get information about built-in integrations."""
    return {
        "framework": "roboco",
        "version": __version__,
        "architecture": "Task → Team → Agent → (Chat, Tool, Memory, Event)",
        "philosophy": "Opinionated framework with freedom of extensibility",
        "integrations": BUILTIN_INTEGRATIONS,
        "features": [
            "Sub-90ms code execution with Daytona",
            "Intelligent memory with Mem0",
            "Built-in web search with SERP",
            "Superior content extraction with Firecrawl",
            "AI-first browser automation with browser-use",
            "MCP tool protocol support",
            "Real-time event system",
            "Unified Agent/Team classes",
            "Type-safe configuration"
        ]
    } 