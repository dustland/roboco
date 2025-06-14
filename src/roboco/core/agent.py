"""
Unified Agent class - the heart of Roboco's agent framework.

This replaces AG2's ConversableAgent with a cleaner, more elegant design.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Literal, Union
from dataclasses import dataclass, field
from enum import Enum

from .brain import Brain, Message, BrainConfig
from .tool import Tool, ToolRegistry
from .memory import Memory
from .event import Event, EventBus

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Agent role types."""
    ASSISTANT = "assistant"  # AI agent
    USER = "user"           # Human user proxy
    SYSTEM = "system"       # System agent


@dataclass
class AgentConfig:
    """Agent configuration."""
    name: str
    role: AgentRole = AgentRole.ASSISTANT
    system_message: str = "You are a helpful AI assistant."
    description: str = ""
    
    # Brain configuration
    brain_config: Optional[BrainConfig] = None
    
    # Capabilities
    enable_code_execution: bool = False
    enable_human_interaction: bool = False
    enable_memory: bool = True
    
    # Behavior
    max_consecutive_replies: int = 10
    auto_reply: bool = True
    silent: bool = False
    
    # Code execution (Daytona)
    code_execution_config: Optional[Dict[str, Any]] = None
    
    # Human interaction
    human_input_mode: Literal["ALWAYS", "NEVER", "TERMINATE"] = "TERMINATE"


class Agent:
    """
    Unified Agent class - clean, modern, and elegant.
    
    This single class handles all agent types (assistant, user, system)
    and integrates all capabilities (brain, tools, memory, events, code execution).
    """
    
    def __init__(self, config: Union[AgentConfig, Dict[str, Any]]):
        # Convert dict to config if needed
        if isinstance(config, dict):
            config = AgentConfig(**config)
        
        self.config = config
        self.name = config.name
        self.role = config.role
        self.system_message = config.system_message
        self.description = config.description or f"{config.role.value.title()} agent: {config.name}"
        
        # Initialize core components
        self.brain = Brain(agent=self, config=config.brain_config)
        self.tools = ToolRegistry(agent=self)
        self.memory = Memory(agent=self) if config.enable_memory else None
        self.events = EventBus(agent=self)
        
        # State management
        self._active = False
        self._conversation_count = 0
        self._last_message: Optional[Message] = None
        
        # Code execution (optional)
        self._code_executor = None
        if config.enable_code_execution:
            self._init_code_executor()
        
        logger.info(f"Created {self.role.value} agent: {self.name}")
    
    @property
    def is_user_agent(self) -> bool:
        """Check if this is a user agent."""
        return self.role == AgentRole.USER
    
    @property
    def is_assistant_agent(self) -> bool:
        """Check if this is an assistant agent."""
        return self.role == AgentRole.ASSISTANT
    
    @property
    def is_system_agent(self) -> bool:
        """Check if this is a system agent."""
        return self.role == AgentRole.SYSTEM
    
    @property
    def is_active(self) -> bool:
        """Check if agent is currently active in conversation."""
        return self._active
    
    def activate(self):
        """Activate the agent."""
        self._active = True
        self.events.emit("agent.activated", {"agent": self.name})
    
    def deactivate(self):
        """Deactivate the agent."""
        self._active = False
        self.events.emit("agent.deactivated", {"agent": self.name})
    
    async def send_message(
        self, 
        content: str, 
        recipient: "Agent",
        request_reply: bool = True,
        **kwargs
    ) -> Optional[Message]:
        """Send a message to another agent."""
        message = Message(
            content=content,
            sender=self.name,
            recipient=recipient.name,
            role=self.role.value,
            **kwargs
        )
        
        # Emit event
        self.events.emit("message.sent", {
            "message": message,
            "sender": self.name,
            "recipient": recipient.name
        })
        
        # Send to recipient
        response = await recipient.receive_message(message, request_reply=request_reply)
        
        return response
    
    async def receive_message(
        self, 
        message: Message, 
        request_reply: bool = True
    ) -> Optional[Message]:
        """Receive a message from another agent."""
        self._last_message = message
        
        # Emit event
        self.events.emit("message.received", {
            "message": message,
            "sender": message.sender,
            "recipient": self.name
        })
        
        # Generate reply if requested
        if request_reply and self.config.auto_reply:
            return await self.generate_reply(message)
        
        return None
    
    async def generate_reply(self, message: Message) -> Optional[Message]:
        """Generate a reply to a message."""
        if not self.config.auto_reply:
            return None
        
        # Check consecutive reply limit
        if self._conversation_count >= self.config.max_consecutive_replies:
            if self.config.human_input_mode == "TERMINATE":
                return await self._handle_human_input("Max replies reached. Continue?")
            return None
        
        # Handle based on agent role
        if self.is_user_agent:
            return await self._generate_user_reply(message)
        elif self.is_assistant_agent:
            return await self._generate_assistant_reply(message)
        else:
            return await self._generate_system_reply(message)
    
    async def _generate_user_reply(self, message: Message) -> Optional[Message]:
        """Generate reply for user agent (human input)."""
        if self.config.enable_human_interaction:
            return await self._handle_human_input("Your response:")
        return None
    
    async def _generate_assistant_reply(self, message: Message) -> Optional[Message]:
        """Generate reply for assistant agent using Brain."""
        # Use the Brain to think and generate response
        messages = [message]  # In real implementation, this would include conversation history
        
        # Let the Brain think and generate response
        response = await self.brain.think(
            messages=messages,
            context={
                "system_message": self.system_message,
                "agent_name": self.name,
                "conversation_count": self._conversation_count
            }
        )
        
        # Update conversation count
        self._conversation_count += 1
        
        return response
    
    async def _generate_system_reply(self, message: Message) -> Optional[Message]:
        """Generate reply for system agent."""
        # System agents typically don't reply unless specifically programmed
        return None
    
    async def _handle_human_input(self, prompt: str) -> Optional[Message]:
        """Handle human input for user agents."""
        if not self.config.enable_human_interaction:
            return None
        
        try:
            # In a real implementation, this would use a proper input interface
            user_input = input(f"{prompt} ")
            
            if user_input.lower() in ["exit", "quit", "stop"]:
                return None
            
            return Message(
                content=user_input,
                sender=self.name,
                recipient="",  # Will be set by caller
                role=self.role.value
            )
        except (EOFError, KeyboardInterrupt):
            return None
    
    async def _handle_code_execution(self, content: str) -> Optional[str]:
        """Handle code execution if enabled."""
        if not self._code_executor:
            return None
        
        # Extract code blocks from content
        # This is a simplified version
        if "```" in content:
            # Extract and execute code
            # Implementation would use Daytona
            return "Code execution result would go here"
        
        return None
    
    def _init_code_executor(self):
        """Initialize code executor (Daytona)."""
        try:
            # This would initialize Daytona code executor
            # For now, just set a flag
            self._code_executor = True
            logger.info(f"Code execution enabled for {self.name}")
        except Exception as e:
            logger.warning(f"Failed to initialize code executor: {e}")
            self._code_executor = None
    
    def add_tool(self, tool: Tool):
        """Add a tool to this agent."""
        self.tools.register(tool)
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from this agent."""
        self.tools.unregister(tool_name)
    
    def save_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Save content to memory."""
        if self.memory:
            self.memory.save(content, metadata)
    
    def search_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search memory."""
        if self.memory:
            return self.memory.search(query)
        return []
    
    def reset(self):
        """Reset agent state."""
        self.brain.clear_thinking_history()
        self._conversation_count = 0
        self._last_message = None
        self._active = False
        
        self.events.emit("agent.reset", {"agent": self.name})
    
    def __str__(self) -> str:
        return f"Agent({self.name}, {self.role.value})"
    
    def __repr__(self) -> str:
        return f"Agent(name='{self.name}', role={self.role.value}, active={self._active})"


# Factory functions for convenience
def create_assistant_agent(
    name: str,
    system_message: str = "You are a helpful AI assistant.",
    **kwargs
) -> Agent:
    """Create an assistant agent."""
    config = AgentConfig(
        name=name,
        role=AgentRole.ASSISTANT,
        system_message=system_message,
        **kwargs
    )
    return Agent(config)


def create_user_agent(
    name: str,
    enable_human_interaction: bool = True,
    **kwargs
) -> Agent:
    """Create a user agent."""
    config = AgentConfig(
        name=name,
        role=AgentRole.USER,
        enable_human_interaction=enable_human_interaction,
        auto_reply=False,  # User agents typically don't auto-reply
        **kwargs
    )
    return Agent(config)


def create_code_agent(
    name: str,
    system_message: str = "You are a helpful AI assistant with code execution capabilities.",
    **kwargs
) -> Agent:
    """Create an assistant agent with code execution enabled."""
    config = AgentConfig(
        name=name,
        role=AgentRole.ASSISTANT,
        system_message=system_message,
        enable_code_execution=True,
        **kwargs
    )
    return Agent(config) 