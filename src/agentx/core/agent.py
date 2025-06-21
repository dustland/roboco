from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum
import json
import asyncio

from .brain import Brain, BrainMessage, BrainResponse
from .config import AgentConfig, BrainConfig
from .message import TaskStep, TextPart, ToolCallPart, ToolResultPart
from .tool import get_tool_schemas, Tool, get_tool_registry
from ..utils.logger import get_logger

logger = get_logger(__name__)


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
    
    def __init__(self, config: AgentConfig, tool_manager=None):
        """
        Initialize agent with configuration and optional tool manager.
        
        Args:
            config: Agent configuration
            tool_manager: Optional tool manager (injected by TaskExecutor)
        """
        # Core configuration
        self.config = config
        self.name = config.name
        self.description = config.description
        self.tools = config.tools or []
        self.memory_enabled = getattr(config, 'memory_enabled', True)  # Default to True if not specified
        self.max_iterations = getattr(config, 'max_iterations', 10)  # Default to 10 if not specified
        
        # State management
        self.state = AgentState(agent_name=self.name)
        
        # Initialize brain with agent's brain config or default
        brain_config = config.brain_config or BrainConfig()
        self.brain = Brain(brain_config)
        
        # Tool management (injected by TaskExecutor for task isolation)
        self.tool_manager = tool_manager
        
        # Validate tool configuration against brain capabilities
        if self.tools and brain_config.supports_function_calls is False:
            logger.warning(
                f"Agent '{self.name}' is configured with {len(self.tools)} tools but the brain model "
                f"'{brain_config.model}' is set to not support function calling. Tools may not work as expected. "
                f"Consider using a model that supports function calling or removing tools from agent configuration."
            )
        
        logger.info(f"🤖 Agent '{self.name}' initialized with {len(self.tools)} tools")
    
    def get_tools_json(self) -> List[Dict[str, Any]]:
        """Get the JSON schemas for the tools available to this agent."""
        if not self.tools or not self.tool_manager:
            return []
        return self.tool_manager.get_tool_schemas(self.tools)

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
        Generate response with tool execution handled by orchestrator.
        
        This is a simpler, non-streaming version that returns the final response.
        
        Args:
            messages: Conversation messages in LLM format
            system_prompt: Optional system prompt override
            orchestrator: Orchestrator instance for tool execution
            max_tool_rounds: Maximum tool execution rounds
            
        Returns:
            Final response string
        """
        self.state.is_active = True
        try:
            # Check if brain config has streaming setting
            if hasattr(self.brain.config, 'streaming') and not self.brain.config.streaming:
                return await self._generate_response_non_streaming(
                    messages, system_prompt, orchestrator, max_tool_rounds
                )
            
            # Use streaming mode (existing behavior)
            response_parts = []
            async for chunk in self._streaming_loop(messages, system_prompt, orchestrator, max_tool_rounds):
                if isinstance(chunk, dict) and chunk.get("type") == "content":
                    response_parts.append(chunk.get("content", ""))
                elif isinstance(chunk, str):
                    response_parts.append(chunk)
            return "".join(response_parts)
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
                
                # Execute tools - use injected ToolExecutor from TaskExecutor
                tool_messages = await self.tool_manager.execute_tool_calls(llm_response.tool_calls, self.name)
                conversation.extend(tool_messages)
                
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
        Clean streaming loop that consumes Brain's structured stream.
        
        The Brain handles all streaming + tool call complexity.
        Agent just processes the structured chunks and handles tool execution.
        """
        conversation = messages.copy()
        available_tools = self.get_tools_json()
        
        for round_num in range(max_tool_rounds):
            # Single streaming call - Brain handles tool call detection
            stream = self.brain.stream_response(
                messages=conversation,
                system_prompt=system_prompt,
                tools=available_tools
            )
            
            # Process structured stream from Brain
            content_parts = []
            tool_calls_detected = []
            
            async for chunk in stream:
                chunk_type = chunk.get('type')
                
                if chunk_type == 'text-delta':
                    # Stream text content to user immediately
                    content = chunk.get('content', '')
                    content_parts.append(content)
                    yield {"type": "content", "content": content}
                    
                elif chunk_type == 'tool-call':
                    # Collect tool calls (no text parsing needed!)
                    tool_calls_detected.append(chunk.get('tool_call'))
                    
                elif chunk_type == 'finish':
                    # Stream finished - process any tool calls
                    break
                    
                elif chunk_type == 'error':
                    # Stream error
                    yield {"type": "error", "content": chunk.get('content', 'Error occurred')}
                    return
            
            # Handle tool calls if detected
            if tool_calls_detected:
                # Emit tool call chunk
                yield {
                    "type": "tool_calls_start", 
                    "count": len(tool_calls_detected),
                    "content": f"\n🔧 Executing {len(tool_calls_detected)} tool(s)...\n"
                }
                
                # Add assistant message with tool calls
                full_content = ''.join(content_parts)
                conversation.append({
                    "role": "assistant",
                    "content": full_content,
                    "tool_calls": [
                        {
                            "id": tc.get('id'),
                            "type": tc.get('type', 'function'),
                            "function": tc.get('function', {})
                        } for tc in tool_calls_detected
                    ]
                })
                
                # Execute tools and emit tool-result chunks for client visualization
                # Convert to expected format for tool executor
                formatted_tool_calls = []
                for tc in tool_calls_detected:
                    # Create mock tool call object with required attributes
                    class MockToolCall:
                        def __init__(self, data):
                            self.id = data.get('id')
                            self.type = data.get('type', 'function')
                            self.function = type('obj', (object,), {
                                'name': data.get('function', {}).get('name'),
                                'arguments': data.get('function', {}).get('arguments')
                            })()
                    
                    formatted_tool_calls.append(MockToolCall(tc))
                
                # Execute tools one by one and emit results for client visualization
                tool_messages = []
                for i, tool_call in enumerate(formatted_tool_calls):
                    # Emit tool call start
                    yield {
                        "type": "tool_call",
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                        "content": f"🔧 Calling {tool_call.function.name}..."
                    }
                    
                    try:
                        # Execute single tool call
                        result = await self.tool_manager.execute_tool_calls([tool_call], self.name)
                        tool_messages.extend(result)
                        
                        # Emit tool result chunk
                        tool_result_content = result[0].get('content', '') if result else 'No result'
                        yield {
                            "type": "tool_result",
                            "name": tool_call.function.name,
                            "success": True,
                            "content": f"✅ {tool_call.function.name}: {tool_result_content[:100]}{'...' if len(tool_result_content) > 100 else ''}"
                        }
                        
                    except Exception as e:
                        # Handle tool execution error
                        error_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": f"Error: {str(e)}"
                        }
                        tool_messages.append(error_message)
                        yield {
                            "type": "tool_result",
                            "name": tool_call.function.name,
                            "success": False,
                            "content": f"❌ {tool_call.function.name} failed: {str(e)}"
                        }
                
                conversation.extend(tool_messages)
                
                # Continue to next step
                continue
            else:
                # No tool calls - conversation complete
                return
        
        # Max rounds exceeded
        yield {"type": "warning", "content": "\n⚠️ Reached maximum tool execution limit."}

    async def _generate_response_non_streaming(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str],
        orchestrator,
        max_tool_rounds: int = 10
    ) -> str:
        """
        Non-streaming loop using Brain's generate_response method.
        """
        conversation = messages.copy()
        available_tools = self.get_tools_json()
        
        for round_num in range(max_tool_rounds):
            # Single non-streaming call
            response = await self.brain.generate_response(
                messages=conversation,
                system_prompt=system_prompt,
                tools=available_tools
            )
            
            # Check if there are tool calls in the response
            if response.tool_calls:
                # Add assistant message with tool calls
                conversation.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tc.get('id'),
                            "type": tc.get('type', 'function'),
                            "function": tc.get('function', {})
                        } for tc in response.tool_calls
                    ]
                })
                
                # Execute tools
                formatted_tool_calls = []
                for tc in response.tool_calls:
                    class MockToolCall:
                        def __init__(self, data):
                            self.id = data.get('id')
                            self.type = data.get('type', 'function')
                            self.function = type('obj', (object,), {
                                'name': data.get('function', {}).get('name'),
                                'arguments': data.get('function', {}).get('arguments')
                            })()
                    
                    formatted_tool_calls.append(MockToolCall(tc))
                
                # Execute tools and add results to conversation
                try:
                    tool_messages = await self.tool_manager.execute_tool_calls(formatted_tool_calls, self.name)
                    conversation.extend(tool_messages)
                except Exception as e:
                    # Handle tool execution error
                    error_message = {
                        "role": "tool",
                        "content": f"Error executing tools: {str(e)}"
                    }
                    conversation.append(error_message)
                
                # Continue to next round
                continue
            else:
                # No tool calls - return the response content
                return response.content or ""
        
        # Max rounds exceeded
        return "Reached maximum tool execution limit."

    def build_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Build the system prompt for the agent, including dynamic context and tool definitions."""
        base_prompt = self.config.prompt_template
        
        if not context:
            return base_prompt
        
        # Add context information
        current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
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