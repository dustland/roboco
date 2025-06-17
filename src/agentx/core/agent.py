from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum
import json
import asyncio

from .brain import Brain, LLMMessage, LLMResponse
from .config import AgentConfig, BrainConfig
from .message import TaskStep, TextPart, ToolCallPart, ToolResultPart
from .tool import get_tool_schemas, Tool, get_tool_registry
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
    Represents an autonomous agent that manages its own conversation flow.
    
    Key Principles:
    - Each agent is autonomous and manages its own conversation flow
    - Agents communicate with other agents through public interfaces only
    - The brain is private to the agent - no external access
    - Tool execution is handled by orchestrator for security and control
    
    This combines:
    - AgentConfig (configuration data)
    - Brain (private LLM interaction)
    - Conversation management (delegates tool execution to orchestrator)
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
        
        # Initialize Brain (PRIVATE to this agent)
        brain_config = config.brain_config or BrainConfig()
        self.brain = Brain(brain_config)
        
        # Agent state
        self.state = AgentState(agent_name=config.name)
        
        # Agent capabilities - start with all registered tools, then add configured tools
        from agentx.tool import list_tools
        self.tools = list_tools()
        self.tools.extend([t for t in config.tools if t not in self.tools])
        self.memory_enabled = getattr(config, 'memory_enabled', True)
        self.max_iterations = getattr(config, 'max_iterations', 10)
        
        logger.info(f"🤖 Agent '{self.name}' initialized with {len(self.tools)} tools")
    
    def get_tools_json(self) -> List[Dict[str, Any]]:
        """Get the JSON schemas for the tools available to this agent."""
        if not self.tools:
            return []
        return get_tool_schemas(self.tools)

    # ============================================================================
    # PUBLIC AGENT INTERFACE - Same as Brain interface for consistency
    # ============================================================================

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        orchestrator = None,
        max_tool_rounds: int = 10
    ) -> str:
        """
        Generate a complete response with tool execution handled by orchestrator.
        
        This matches Brain's interface but includes tool execution loop.
        
        Args:
            messages: Conversation messages in LLM format
            system_prompt: Optional system prompt override
            orchestrator: Orchestrator instance for tool execution
            max_tool_rounds: Maximum tool execution rounds
            
        Returns:
            Complete response after all tool executions
        """
        self.state.is_active = True
        try:
            return await self._conversation_loop(messages, system_prompt, orchestrator, max_tool_rounds)
        finally:
            self.state.is_active = False

    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        orchestrator = None,
        max_tool_rounds: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Stream response with tool execution handled by orchestrator.
        
        This matches Brain's interface but includes tool execution loop.
        
        Args:
            messages: Conversation messages in LLM format
            system_prompt: Optional system prompt override
            orchestrator: Orchestrator instance for tool execution
            max_tool_rounds: Maximum tool execution rounds
            
        Yields:
            Response chunks and tool execution status updates
        """
        self.state.is_active = True
        try:
            async for chunk in self._streaming_loop(messages, system_prompt, orchestrator, max_tool_rounds):
                yield chunk
        finally:
            self.state.is_active = False

    # ============================================================================
    # CONVERSATION MANAGEMENT - Works with orchestrator for tool execution
    # ============================================================================

    async def _conversation_loop(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str],
        orchestrator,
        max_tool_rounds: int = 10
    ) -> str:
        """
        Conversation loop that works with orchestrator for tool execution.
        
        Agent generates responses, orchestrator executes tools for security.
        """
        conversation = messages.copy()
        
        for round_num in range(max_tool_rounds):
            # Get response from brain
            llm_response = await self.brain.generate_response(
                messages=conversation,
                system_prompt=system_prompt,
                tools=self.get_tools_json()
            )
            
            # Check if brain wants to call tools
            if llm_response.tool_calls:
                logger.debug(f"Agent '{self.name}' requesting {len(llm_response.tool_calls)} tool calls in round {round_num + 1}")
                
                # Add assistant's message with tool calls
                conversation.append({
                    "role": "assistant",
                    "content": llm_response.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in llm_response.tool_calls
                    ]
                })
                
                # Orchestrator executes tools for security
                if orchestrator:
                    tool_messages = await orchestrator.execute_tool_calls(llm_response.tool_calls)
                    conversation.extend(tool_messages)
                else:
                    # No orchestrator - add error messages
                    for tc in llm_response.tool_calls:
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": json.dumps({"success": False, "error": "No orchestrator available for tool execution"})
                        })
                
                # Continue to next round
                continue
            else:
                # No tool calls, return final response
                return llm_response.content or ""
        
        # Max rounds exceeded
        logger.warning(f"Agent '{self.name}' exceeded maximum tool execution rounds ({max_tool_rounds})")
        return llm_response.content or "I apologize, but I've reached the maximum number of tool execution attempts."

    async def _streaming_loop(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str],
        orchestrator,
        max_tool_rounds: int = 10
    ) -> AsyncGenerator[str, None]:
        """
        Streaming conversation loop that works with orchestrator for tool execution.
        """
        conversation = messages.copy()
        
        for round_num in range(max_tool_rounds):
            # Get response from brain (non-streaming to check for tool calls)
            llm_response = await self.brain.generate_response(
                messages=conversation,
                system_prompt=system_prompt,
                tools=self.get_tools_json()
            )
            
            # Check if brain wants to call tools
            if llm_response.tool_calls:
                tool_names = [tc.function.name for tc in llm_response.tool_calls]
                yield f"🔧 Executing tools: {', '.join(tool_names)}...\n"
                
                # Add assistant's message with tool calls
                conversation.append({
                    "role": "assistant",
                    "content": llm_response.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in llm_response.tool_calls
                    ]
                })
                
                # Orchestrator executes tools for security
                if orchestrator:
                    tool_messages = await orchestrator.execute_tool_calls(llm_response.tool_calls)
                    conversation.extend(tool_messages)
                else:
                    # No orchestrator - add error messages
                    for tc in llm_response.tool_calls:
                        conversation.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": json.dumps({"success": False, "error": "No orchestrator available for tool execution"})
                        })
                
                yield "✅ Tools executed. Continuing...\n"
                
                # Continue to next round
                continue
            else:
                # No tool calls - stream the final response
                if llm_response.content:
                    # Make a streaming call for the final response
                    async for chunk in self.brain.stream_response(
                        messages=conversation,
                        system_prompt=system_prompt
                    ):
                        yield chunk
                return
        
        # Max rounds exceeded
        yield "I apologize, but I've reached the maximum number of tool execution attempts."

    def build_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Build the system prompt for the agent, including dynamic context and tool definitions."""
        base_prompt = self.config.prompt_template
        
        if not context:
            return base_prompt
        
        # Add context information
        current_datetime = datetime.now().strftime("%A, %B %d, YYYY at %I:%M %p")
        context_prompt = f"""
Here is some context for the current task:
- Current date and time: {current_datetime}
- Task ID: {context.get('task_id', 'N/A')}
- Round: {context.get('round_count', 0)}
- Workspace: {context.get('workspace_dir', 'N/A')}
"""
        
        # Add tool information with explicit instructions
        tools_prompt = ""
        if self.tools:
            available_tools = [tool for tool in self.tools if tool in [t['function']['name'] for t in self.get_tools_json()]]
            if available_tools:
                tools_prompt = f"""

IMPORTANT: You have access to the following tools. Use them when needed to complete tasks:

Available Tools: {', '.join(available_tools)}

When you need to use a tool:
1. Think about which tool would help accomplish the task
2. Call the tool with the appropriate parameters
3. Wait for the result before continuing
4. Use the tool results to inform your response

Tool Usage Guidelines:
- Use tools proactively when they can help solve the user's request
- For file operations, use the file management tools
- For saving important content, use store_artifact
- For research or web searches, use the search tools
- Always check tool results and handle errors gracefully
"""
        
        return f"{base_prompt}{context_prompt}{tools_prompt}"

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities summary."""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "memory_enabled": self.memory_enabled,
            "max_iterations": self.max_iterations,
            "state": self.state.dict()
        }
    
    def reset_state(self):
        """Reset agent state."""
        self.state = AgentState(agent_name=self.name)
    
    def add_tool(self, tool):
        """Add a tool to the agent's capabilities."""
        if isinstance(tool, str):
            if tool not in self.tools:
                self.tools.append(tool)
        elif isinstance(tool, Tool):
            # Register the tool and add its methods
            from .tool import register_tool
            register_tool(tool)
            methods = tool.get_callable_methods()
            for method_name in methods:
                if method_name not in self.tools:
                    self.tools.append(method_name)
        else:
            raise ValueError(f"Invalid tool type: {type(tool)}")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the agent's capabilities."""
        if tool_name in self.tools:
            self.tools.remove(tool_name)
    
    def update_config(self, **kwargs):
        """Update agent configuration."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def __str__(self) -> str:
        return f"Agent(name='{self.name}', tools={len(self.tools)}, active={self.state.is_active})"
    
    def __repr__(self) -> str:
        return self.__str__()


def create_assistant_agent(name: str, system_message: str = "") -> Agent:
    """Create a simple assistant agent with default configuration."""
    from .config import AgentConfig, BrainConfig
    
    config = AgentConfig(
        name=name,
        description="AI Assistant",
        prompt_template=system_message or "You are a helpful AI assistant.",
        brain_config=BrainConfig()
    )
    
    return Agent(config) 