"""
Brain - The Intelligent Thinking Component

The Brain is the core reasoning component of each agent that handles:
- LLM integration and reasoning
- Context management and memory integration
- Tool/function calling orchestration  
- All forms of intelligent response generation

This is where the "thinking" happens.
"""

from ..utils.logger import get_logger
import os
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio
import openai

from ..memory import create_memory_backend, MemoryBackend, MemoryQuery, MemoryType

logger = get_logger(__name__)


@dataclass
class Message:
    """Individual message in a conversation."""
    content: str
    sender: str
    recipient: str = ""
    role: str = "assistant"
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    
    # Optional fields for advanced functionality
    metadata: Dict[str, Any] = field(default_factory=dict)
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    name: Optional[str] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI message format."""
        msg = {"role": self.role, "content": self.content}
        if self.name:
            msg["name"] = self.name
        if self.function_call:
            msg["function_call"] = self.function_call
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        return msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message_id": self.message_id,
            "content": self.content,
            "sender": self.sender,
            "recipient": self.recipient,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "function_call": self.function_call,
            "tool_calls": self.tool_calls,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Create message from dictionary."""
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class BrainConfig:
    """Brain configuration for reasoning and LLM integration."""
    model: str = "deepseek-reasoner"  # Default to reasoning model for best thinking
    api_key: Optional[str] = None
    base_url: Optional[str] = "https://api.deepseek.com"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: int = 30
    
    # Reasoning parameters
    enable_reasoning_traces: bool = True
    enable_memory_integration: bool = True
    enable_tool_calling: bool = True
    
    # Tool execution override - force tool executors to use tool-capable model
    tool_executor_model: str = "deepseek-chat"  # Override for tool execution


class Brain:
    """
    Brain - The intelligent thinking component.
    
    This is where all the "thinking" happens:
    - LLM reasoning and response generation
    - Memory integration and context management
    - Tool calling and function orchestration
    - Complex reasoning workflows
    
    The Brain generates all kinds of intelligent results through reasoning.
    """
    
    def __init__(self, agent: "Agent", config: Optional[BrainConfig] = None):
        self.agent = agent
        self.config = config or BrainConfig()
        
        # Initialize LLM client with DeepSeek support
        api_key = self.config.api_key or os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        
        if self.config.base_url and "deepseek" in self.config.base_url:
            # Use DeepSeek API
            self._llm_client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.base_url
            )
        else:
            # Use OpenAI API
            self._llm_client = openai.AsyncOpenAI(api_key=api_key)
        
        # Thinking state
        self._reasoning_context: Dict[str, Any] = {}
        self._thinking_history: List[Dict[str, Any]] = []
        
        logger.debug(f"Initialized Brain for agent: {self.agent.name} with model: {self.config.model}")
        logger.debug(f"Tool executor will use: {self.config.tool_executor_model}")
    
    async def think(
        self,
        messages: List[Message],
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Message:
        """
        Core thinking method - generates intelligent responses.
        
        Supports both reasoning (DeepSeek-Reasoner) and tool calling (DeepSeek-Chat).
        Tool execution is handled separately by tool executor agents.
        """
        try:
            # Record thinking process
            thinking_step = {
                "timestamp": datetime.now().isoformat(),
                "input_messages": len(messages),
                "context": context or {},
                "agent": self.agent.name,
                "model_used": self.config.model
            }
            
            # Prepare messages for the LLM
            llm_messages = [msg.to_openai_format() for msg in messages]
            if self.agent.system_message:
                llm_messages.insert(0, {"role": "system", "content": self.agent.system_message})

            # Get available tools for this agent (LLM tools only)
            tool_schemas = self.agent.get_tool_schemas() if self.config.enable_tool_calling else []
            
            logger.info(f"🧠 {self.agent.name} thinking with {self.config.model}...")
            if tool_schemas:
                logger.info(f"🔧 Available tools: {[tool['name'] for tool in tool_schemas]}")
            
            # Call LLM with or without tools based on model capability
            if self.config.model == "deepseek-reasoner":
                # DeepSeek-Reasoner doesn't support tools
                llm_response = await self._llm_client.chat.completions.create(
                    model=self.config.model,
                    messages=llm_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
            else:
                # Other models (like deepseek-chat) support tools
                llm_response = await self._llm_client.chat.completions.create(
                    model=self.config.model,
                    messages=llm_messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    tools=tool_schemas if tool_schemas else None,
                    tool_choice="auto" if tool_schemas else None
                )
            
            logger.info(f"🧠 {self.agent.name} received response from {self.config.model}")
            
            response_message = llm_response.choices[0].message
            response_content = response_message.content or ""
            
            # Debug: Log what we actually received
            logger.debug(f"🔍 Response content length: {len(response_content)}")
            logger.debug(f"🔍 Response content preview: {response_content[:100]}...")

            # Check if LLM wants to call tools
            if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                logger.info(f"🔧 {self.agent.name} wants to call {len(response_message.tool_calls)} tools")
                
                # Create tool call message
                tool_calls_data = []
                for tool_call in response_message.tool_calls:
                    tool_calls_data.append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    })
                
                # Return message with tool calls for executor to handle
                response = Message(
                    content=response_content or f"I need to use tools: {[tc.function.name for tc in response_message.tool_calls]}",
                    sender=self.agent.name,
                    role="assistant",
                    tool_calls=tool_calls_data,
                    metadata={
                        "thinking_step": thinking_step,
                        "brain_generated": True,
                        "llm_usage": dict(llm_response.usage),
                        "model_used": self.config.model,
                        "requires_tool_execution": True
                    }
                )
            else:
                # Regular response without tool calls
                response = Message(
                    content=response_content,
                    sender=self.agent.name,
                    role="assistant",
                    metadata={
                        "thinking_step": thinking_step,
                        "brain_generated": True,
                        "llm_usage": dict(llm_response.usage),
                        "model_used": self.config.model
                    }
                )
            
            # Record thinking result
            thinking_step["response_generated"] = True
            thinking_step["response_length"] = len(response.content)
            thinking_step["tool_calls_requested"] = len(response.tool_calls) if response.tool_calls else 0
            self._thinking_history.append(thinking_step)
            
            logger.debug(f"Brain generated response for {self.agent.name}")
            logger.debug(f"🔍 Returning message with content: '{response.content[:100]}...'")
            return response
            
        except Exception as e:
            logger.error(f"Brain thinking failed for {self.agent.name}: {e}")
            return Message(
                content=f"🧠 Thinking error: {str(e)}",
                sender=self.agent.name,
                role="assistant",
                metadata={"error": True, "error_message": str(e)}
            )
    

    
    async def reason_with_tools(
        self,
        messages: List[Message],
        available_tools: Dict[str, Callable],
        **kwargs
    ) -> List[Message]:
        """
        Advanced reasoning with tool integration.
        
        This method is now integrated into the main think() method
        through the hybrid architecture. It's kept for backward compatibility.
        """
        logger.info(f"🧠 {self.agent.name} reason_with_tools called - delegating to hybrid think()")
        
        # Convert to the new architecture
        response = await self.think(messages, context={"available_tools": available_tools})
        return [response] if response else []
    
    async def integrate_memory(
        self,
        messages: List[Message],
        memory_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Integrate memory into thinking process.
        
        The Brain can pull relevant memories and integrate them
        into the reasoning process.
        """
        if not self.config.enable_memory_integration:
            return {}
        
        # Simple memory integration for now
        return {
            "memory_integrated": True,
            "relevant_memories": [],
            "context_enhanced": bool(memory_context)
        }
    
    def get_thinking_history(self) -> List[Dict[str, Any]]:
        """Get the history of thinking processes."""
        return self._thinking_history.copy()
    
    def clear_thinking_history(self):
        """Clear thinking history."""
        self._thinking_history.clear()
        self._reasoning_context.clear()
    
    def __str__(self) -> str:
        return f"Brain({self.agent.name})"
    
    def __repr__(self) -> str:
        return f"Brain(agent={self.agent.name}, model={self.config.model})"


class ChatHistory:
    """Task-level conversation history."""
    
    def __init__(self, task_id: str = ""):
        self.task_id = task_id
        self.messages: List[Message] = []
        self.created_at = datetime.now()
        
    def add_message(self, message: Message) -> None:
        """Add a message to the conversation history."""
        self.messages.append(message)
        
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get messages with optional limit."""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def clear_history(self) -> None:
        """Clear all messages from history."""
        self.messages.clear()
    
    def __len__(self) -> int:
        return len(self.messages)


# Utility functions for creating messages
def create_system_message(content: str, recipient: str = "") -> Message:
    """Create a system message."""
    return Message(
        content=content,
        sender="System",
        recipient=recipient,
        role="system"
    )


def create_user_message(content: str, sender: str, recipient: str = "") -> Message:
    """Create a user message."""
    return Message(
        content=content,
        sender=sender,
        recipient=recipient,
        role="user"
    )


def create_assistant_message(content: str, sender: str, recipient: str = "") -> Message:
    """Create an assistant message."""
    return Message(
        content=content,
        sender=sender,
        recipient=recipient,
        role="assistant"
    )
