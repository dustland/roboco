from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum

from .brain import Brain, LLMMessage, LLMResponse
from .config import AgentConfig, LLMConfig
from .message import TaskStep, TextPart, ToolCallPart, ToolResultPart
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AgentRole(str, Enum):
    """Agent roles for conversation flow."""
    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"


class AgentState(BaseModel):
    """Current state of an agent during execution."""
    agent_name: str
    current_step_id: Optional[str] = None
    is_active: bool = False
    last_response: Optional[str] = None
    last_response_timestamp: Optional[datetime] = None
    tool_calls_made: int = 0
    tokens_used: int = 0
    errors_encountered: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Agent:
    """
    Represents an active agent that can process tasks and generate responses.
    
    This is the main execution class that combines:
    - AgentConfig (configuration data)
    - Brain (LLM interaction)
    - Agent-specific logic and state management
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize agent with configuration.
        
        Args:
            config: Agent configuration containing name, prompts, tools, etc.
        """
        self.config = config
        self.name = config.name
        self.description = config.description
        
        # Initialize Brain with agent's LLM config or default
        llm_config = config.llm_config or LLMConfig()
        self.brain = Brain(llm_config)
        
        # Agent state
        self.state = AgentState(agent_name=config.name)
        
        # Agent capabilities
        self.tools = config.tools.copy()
        self.memory_enabled = getattr(config, 'memory_enabled', True)
        self.max_iterations = getattr(config, 'max_iterations', 10)
        
        logger.info(f"🤖 Agent '{self.name}' initialized with {len(self.tools)} tools")
    
    async def generate_response(
        self,
        task_prompt: str,
        context: Dict[str, Any],
        conversation_history: List[TaskStep],
        system_prompt: Optional[str] = None
    ) -> LLMResponse:
        """
        Generate a response to input messages.
        
        Args:
            task_prompt: The main task prompt
            context: Additional context for the agent
            conversation_history: Previous conversation steps
            system_prompt: Override system prompt (optional)
            
        Returns:
            LLM response with content and metadata
        """
        self.state.is_active = True
        self.state.current_step_id = context.get('step_id')
        
        try:
            # Prepare messages for LLM
            messages = self._prepare_messages(
                task_prompt=task_prompt,
                conversation_history=conversation_history,
                context=context
            )
            
            # Use provided system prompt or agent's default
            if not system_prompt:
                system_prompt = self._build_system_prompt(context)
            
            # Generate response using Brain
            response = await self.brain.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                available_tools=self.tools
            )
            
            # Update agent state
            self.state.last_response = response.content
            self.state.last_response_timestamp = datetime.now()
            self.state.tokens_used += getattr(response, 'tokens_used', 0)
            
            logger.debug(f"Agent '{self.name}' generated response: {len(response.content)} chars")
            return response
            
        except Exception as e:
            self.state.errors_encountered += 1
            logger.error(f"Agent '{self.name}' error: {e}")
            raise
        finally:
            self.state.is_active = False
    
    async def stream_response(
        self,
        task_prompt: str,
        context: Dict[str, Any],
        conversation_history: List[TaskStep],
        system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response to input messages.
        
        Args:
            task_prompt: The main task prompt
            context: Additional context for the agent
            conversation_history: Previous conversation steps
            system_prompt: Override system prompt (optional)
            
        Yields:
            Response chunks as they are generated
        """
        self.state.is_active = True
        self.state.current_step_id = context.get('step_id')
        
        try:
            # Prepare messages for LLM
            messages = self._prepare_messages(
                task_prompt=task_prompt,
                conversation_history=conversation_history,
                context=context
            )
            
            # Use provided system prompt or agent's default
            if not system_prompt:
                system_prompt = self._build_system_prompt(context)
            
            # Stream response using Brain
            response_chunks = []
            async for chunk in self.brain.stream_response(
                messages=messages,
                system_prompt=system_prompt
            ):
                response_chunks.append(chunk)
                yield chunk
            
            # Update agent state with complete response
            complete_response = "".join(response_chunks)
            self.state.last_response = complete_response
            self.state.last_response_timestamp = datetime.now()
            
            logger.debug(f"Agent '{self.name}' streamed response: {len(complete_response)} chars")
            
        except Exception as e:
            self.state.errors_encountered += 1
            logger.error(f"Agent '{self.name}' streaming error: {e}")
            raise
        finally:
            self.state.is_active = False
    
    def _prepare_messages(
        self,
        task_prompt: str,
        conversation_history: List[TaskStep],
        context: Dict[str, Any]
    ) -> List[LLMMessage]:
        """Prepare messages for LLM based on conversation history."""
        messages = []
        
        # Add initial task prompt
        messages.append(LLMMessage(
            role="user",
            content=task_prompt,
            timestamp=datetime.now()
        ))
        
        # Add conversation history
        for step in conversation_history:
            for part in step.parts:
                if isinstance(part, TextPart):
                    # Determine role based on agent
                    role = "assistant" if step.agent_name == self.name else "user"
                    messages.append(LLMMessage(
                        role=role,
                        content=part.text,
                        timestamp=step.timestamp
                    ))
        
        return messages
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt from agent configuration and context."""
        # Start with base prompt template
        base_prompt = getattr(self.config, 'prompt_template', '') or "You are a helpful AI assistant."
        
        # Add agent description
        if self.description:
            base_prompt += f"\n\nAgent Description: {self.description}"
        
        # Add available tools information
        if self.tools:
            tools_info = f"\n\nAvailable Tools: {', '.join(self.tools)}"
            base_prompt += tools_info
        
        # Add context information
        if context.get('available_tools'):
            tools_context = f"\n\nTool Schemas: {context['available_tools']}"
            base_prompt += tools_context
        
        if context.get('handoff_targets'):
            handoff_info = f"\n\nHandoff Targets: {', '.join(context['handoff_targets'])}"
            base_prompt += handoff_info
        
        return base_prompt
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and current state."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "memory_enabled": self.memory_enabled,
            "max_iterations": self.max_iterations,
            "state": self.state.dict(),
            "llm_model": self.brain.config.model
        }
    
    def reset_state(self):
        """Reset agent state for new task."""
        self.state = AgentState(agent_name=self.name)
        logger.debug(f"Agent '{self.name}' state reset")
    
    def add_tool(self, tool):
        """Add a tool to the agent's toolset.
        
        Args:
            tool: Tool function or tool name to add
        """
        if callable(tool):
            # If it's a function, add it to the tools list
            tool_name = getattr(tool, '__name__', str(tool))
            self.tools.append(tool)
            logger.debug(f"Added tool function '{tool_name}' to agent '{self.name}'")
        elif isinstance(tool, str):
            # If it's a string, add it to the tools list
            if tool not in self.tools:
                self.tools.append(tool)
                logger.debug(f"Added tool '{tool}' to agent '{self.name}'")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent's capabilities."""
        if tool_name in self.tools:
            self.tools.remove(tool_name)
            logger.info(f"Tool '{tool_name}' removed from agent '{self.name}'")
    
    def update_config(self, **kwargs):
        """Update agent configuration dynamically."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.debug(f"Agent '{self.name}' config updated: {key} = {value}")
    
    def __str__(self) -> str:
        return f"Agent(name='{self.name}', tools={len(self.tools)}, active={self.state.is_active})"
    
    def __repr__(self) -> str:
        return self.__str__()

def create_assistant_agent(name: str, system_message: str = "") -> Agent:
    """
    Backwards compatibility function to create a basic assistant agent.
    """
    return Agent(
        name=name,
        system_message=system_message or "You are a helpful assistant."
    ) 