"""
Brain Component - Pure LLM Gateway

Handles all LLM interactions for agents, including provider abstraction,
prompt formatting, and response parsing. Does NOT handle tool execution -
that's the orchestrator's responsibility.
"""

import os
import asyncio
import json
from typing import Dict, Any, List, Optional, Union, AsyncGenerator
from datetime import datetime
from pydantic import BaseModel, Field
import litellm

from ..utils.logger import get_logger
from .config import BrainConfig

logger = get_logger(__name__)


class BrainMessage(BaseModel):
    """Standard message format for brain interactions."""
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # For tool responses
    timestamp: Optional[datetime] = None


class BrainResponse(BaseModel):
    """Response from brain call, which can be either text content or a request to call tools."""
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    timestamp: datetime


class Brain:
    """
    Brain component that handles all LLM interactions for an agent.
    
    This is a PURE LLM interface - it does not execute tools or handle
    conversation flow. Those responsibilities belong to the orchestrator.
    
    The Brain's only job is:
    1. Format messages for the LLM
    2. Make API calls
    3. Parse and return responses
    """
    
    def __init__(self, config: BrainConfig):
        """
        Initialize Brain with Brain configuration.
        
        Args:
            config: Brain configuration including provider, model, etc.
        """
        self.config = config
        self.initialized = False
        self._usage_callbacks = []
    
    @classmethod
    def from_config(cls, brain_config: BrainConfig) -> "Brain":
        """Create Brain instance from configuration."""
        return cls(brain_config)
        
    def add_usage_callback(self, callback):
        """
        Add a callback function to be called after each LLM request.
        
        The callback will be called with (model, usage_data, response) parameters.
        - For streaming: callback(model, usage_data, None)
        - For non-streaming: callback(model, None, response)
        
        Args:
            callback: Function to call with usage data
        """
        self._usage_callbacks.append(callback)
    
    def remove_usage_callback(self, callback):
        """Remove a usage callback."""
        if callback in self._usage_callbacks:
            self._usage_callbacks.remove(callback)
    
    def _notify_usage_callbacks(self, model: str, usage_data=None, response=None):
        """Notify all registered usage callbacks."""
        for callback in self._usage_callbacks:
            try:
                callback(model, usage_data, response)
            except Exception as e:
                logger.warning(f"Usage callback failed: {e}")
        
    async def _ensure_initialized(self):
        if not self.initialized:
            # Validate function calling support if tools will be used
            if self.config.supports_function_calls:
                await self._validate_function_calling_support()
            
            self.initialized = True
            logger.info(f"LLM client for '{self.config.model}' initialized.")

    async def _validate_function_calling_support(self):
        """Validate that the model actually supports function calling."""
        # Get the full model name as it would be used in API calls
        model_name = self.config.model
        if hasattr(self.config, 'provider') and self.config.provider and '/' not in model_name:
            model_name = f"{self.config.provider}/{self.config.model}"
        
        try:
            # Check if LiteLLM reports the model supports function calling
            supports_fc = litellm.supports_function_calling(model=model_name)
            
            if not supports_fc:
                logger.warning(
                    f"Model '{model_name}' does not support native function calling according to LiteLLM. "
                    f"Function calls will be handled via text-based fallback method."
                )
                # Update config to reflect actual capabilities
                self.config.supports_function_calls = False
            else:
                logger.info(f"Model '{model_name}' supports native function calling.")
                
        except Exception as e:
            logger.warning(
                f"Could not validate function calling support for '{model_name}': {e}. "
                f"Assuming text-based tool calling."
            )
            # Be conservative - assume no native support if we can't validate
            self.config.supports_function_calls = False

    def _format_messages(self, messages: List[Dict[str, Any]], system_prompt: Optional[str] = None) -> List[Dict[str, Any]]:
        """Format messages for LLM call."""
        formatted_messages = []
        
        if system_prompt:
            # Always append current date/time to system prompt
            current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
            enhanced_system_prompt = f"{system_prompt}\n\nCurrent date and time: {current_datetime}"
            formatted_messages.append({
                "role": "system", 
                "content": enhanced_system_prompt
            })
        
        formatted_messages.extend(messages)
        return formatted_messages

    def _prepare_call_params(self, messages: List[Dict[str, Any]], temperature: Optional[float] = None, 
                           tools: Optional[List[Dict[str, Any]]] = None, stream: bool = False) -> Dict[str, Any]:
        """Prepare parameters for LLM API call."""
        # Handle model name - if it already includes provider prefix, use as-is
        model_name = self.config.model
        if hasattr(self.config, 'provider') and self.config.provider and '/' not in model_name:
            model_name = f"{self.config.provider}/{self.config.model}"
        
        call_params = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature or self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.timeout,
            "stream": stream
        }
        
        # For streaming calls, request usage data in the final chunk
        if stream:
            call_params["stream_options"] = {"include_usage": True}
        
        # Add API credentials and base URL
        if self.config.api_key:
            call_params["api_key"] = self.config.api_key
        if self.config.base_url:
            call_params["api_base"] = self.config.base_url
            
        # Add tools if model supports native function calling
        if tools and self.config.supports_function_calls:
            call_params["tools"] = tools
            call_params["tool_choice"] = "auto"
        elif tools and not self.config.supports_function_calls:
            logger.warning(
                f"Tools were provided but model '{model_name}' does not support native function calling. "
                f"Tools will be ignored for this call. Consider using a model that supports function calling "
                f"or implement text-based tool calling."
            )
            
        return call_params

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> BrainResponse:
        """
        Generate a single response from the LLM.
        
        This is a PURE LLM call - no tool execution, no conversation management.
        If the LLM requests tool calls, they are returned in the response for
        the orchestrator to handle.
        
        Args:
            messages: Conversation history
            system_prompt: Optional system prompt
            temperature: Override temperature
            tools: Available tools for the LLM
            
        Returns:
            LLM response (may contain tool call requests)
        """
        await self._ensure_initialized()
        

        
        formatted_messages = self._format_messages(messages, system_prompt)
        call_params = self._prepare_call_params(formatted_messages, temperature, tools, stream=False)
        
        try:
            logger.debug(f"Making LLM call with {len(formatted_messages)} messages")
            
            response = await litellm.acompletion(**call_params)
            message = response.choices[0].message
            
            # Notify usage callbacks
            self._notify_usage_callbacks(response.model, None, response)
            
            return BrainResponse(
                content=message.content,
                tool_calls=message.tool_calls if hasattr(message, 'tool_calls') else None,
                model=response.model,
                usage=response.usage.dict() if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return BrainResponse(
                content=f"I apologize, but I encountered an error: {str(e)}", 
                model=self.config.model or "unknown", 
                finish_reason="error",
                timestamp=datetime.now()
            )

    async def stream_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response from the LLM with integrated tool call detection.
        
        Handles both native function calling models and text-based tool calling,
        always emitting structured tool-call and tool-result chunks for client visualization.
        
        Args:
            messages: Conversation history
            system_prompt: Optional system prompt  
            temperature: Override temperature
            tools: Available tools for the LLM
            
        Yields:
            Dict[str, Any]: Structured chunks with type and data:
            - {'type': 'text-delta', 'content': str} - Text content chunks
            - {'type': 'tool-call', 'tool_call': obj} - Tool call requests
            - {'type': 'tool-result', 'tool_call_id': str, 'result': any} - Tool results
            - {'type': 'finish', 'finish_reason': str} - Stream completion
            - {'type': 'error', 'content': str} - Error messages
        """
        await self._ensure_initialized()
        

        
        formatted_messages = self._format_messages(messages, system_prompt)
        call_params = self._prepare_call_params(formatted_messages, temperature, tools, stream=True)
        
        try:
            logger.debug(f"Making streaming LLM call with {len(formatted_messages)} messages")
            
            # Debug: Log the exact tool schemas being sent
            if tools:
                logger.info(f"[BRAIN] Sending {len(tools)} tools to LLM:")
                for i, tool in enumerate(tools):
                    logger.info(f"[BRAIN] Tool {i+1}: {tool}")
            else:
                logger.info(f"[BRAIN] No tools being sent to LLM")
            
            response = await litellm.acompletion(**call_params)
            
            if self.config.supports_function_calls and tools:
                # Native function calling mode
                async for chunk in self._handle_native_function_calling_stream(response):
                    yield chunk
            else:
                # Text-based tool calling mode (for models without native support)
                async for chunk in self._handle_text_based_tool_calling_stream(response, tools):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Streaming LLM call failed: {e}")
            yield {
                'type': 'error',
                'content': f"I apologize, but I encountered an error: {str(e)}"
            }
    
    async def _handle_native_function_calling_stream(self, response) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming for models with native function calling support."""
        # Track accumulated tool calls for proper reconstruction
        accumulated_tool_calls = {}
        usage_data = None
        model_name = None
        
        async for chunk in response:
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue
                
            delta = choice.delta
            
            # Capture model name and usage data when available
            if hasattr(chunk, 'model') and chunk.model:
                model_name = chunk.model
            if hasattr(chunk, 'usage') and chunk.usage:
                # Handle different usage object formats
                if hasattr(chunk.usage, 'model_dump'):
                    usage_data = chunk.usage.model_dump()
                elif hasattr(chunk.usage, 'dict'):
                    usage_data = chunk.usage.dict()
                else:
                    usage_data = chunk.usage
            
            # Handle text content streaming
            if hasattr(delta, 'content') and delta.content:
                yield {
                    'type': 'text-delta',
                    'content': delta.content
                }
            
            # Handle tool calls (structured data from native function calling)
            if hasattr(delta, 'tool_calls') and delta.tool_calls:
                logger.info(f"[BRAIN] Received tool calls delta: {delta.tool_calls}")
                for tool_call_delta in delta.tool_calls:
                    logger.info(f"[BRAIN] Processing tool call delta: {tool_call_delta}")
                    tool_call_id = getattr(tool_call_delta, 'id', None)
                    
                    if tool_call_id:
                        # Initialize new tool call with ID
                        if tool_call_id not in accumulated_tool_calls:
                            accumulated_tool_calls[tool_call_id] = {
                                'id': tool_call_id,
                                'type': getattr(tool_call_delta, 'type', 'function'),
                                'function': {
                                    'name': '',
                                    'arguments': ''
                                }
                            }
                            logger.info(f"[BRAIN] Initialized tool call: {tool_call_id}")
                        
                        # Accumulate function name and arguments for this specific tool call
                        if hasattr(tool_call_delta, 'function'):
                            func = tool_call_delta.function
                            if hasattr(func, 'name') and func.name:
                                accumulated_tool_calls[tool_call_id]['function']['name'] = func.name
                                logger.info(f"[BRAIN] Set function name: {func.name}")
                            if hasattr(func, 'arguments') and func.arguments is not None:
                                accumulated_tool_calls[tool_call_id]['function']['arguments'] += func.arguments
                                logger.info(f"[BRAIN] Added arguments: '{func.arguments}' -> Total: '{accumulated_tool_calls[tool_call_id]['function']['arguments']}'")
                            else:
                                logger.info(f"[BRAIN] No arguments in this delta")
                    
                    elif hasattr(tool_call_delta, 'function') and accumulated_tool_calls:
                        # Handle chunks without ID - accumulate to the most recent tool call
                        # This handles DeepSeek's pattern where first chunk has ID, subsequent chunks don't
                        most_recent_id = list(accumulated_tool_calls.keys())[-1]
                        func = tool_call_delta.function
                        
                        if hasattr(func, 'name') and func.name:
                            accumulated_tool_calls[most_recent_id]['function']['name'] = func.name
                            logger.info(f"[BRAIN] Set function name (no ID): {func.name}")
                        if hasattr(func, 'arguments') and func.arguments is not None:
                            accumulated_tool_calls[most_recent_id]['function']['arguments'] += func.arguments
                            logger.info(f"[BRAIN] Added arguments (no ID): '{func.arguments}' -> Total: '{accumulated_tool_calls[most_recent_id]['function']['arguments']}'")
                        else:
                            logger.info(f"[BRAIN] No arguments in this delta (no ID)")
            
            # Handle finish reason - emit complete tool calls
            if hasattr(choice, 'finish_reason') and choice.finish_reason:
                logger.debug(f"[BRAIN] Stream finished, accumulated tool calls: {accumulated_tool_calls}")
                # Emit all accumulated tool calls for client visualization
                for tool_call in accumulated_tool_calls.values():
                    if tool_call['function']['name']:  # Only emit complete tool calls
                        logger.debug(f"[BRAIN] Emitting tool call: {tool_call}")
                        yield {
                            'type': 'tool-call',
                            'tool_call': tool_call
                        }
                
                # For tool_calls finish reason, continue processing to get usage data
                if choice.finish_reason == 'tool_calls':
                    continue  # Don't yield finish yet, wait for usage data
                
                # Notify usage callbacks before yielding finish
                if usage_data and model_name:
                    self._notify_usage_callbacks(model_name, usage_data, None)
                
                yield {
                    'type': 'finish',
                    'finish_reason': choice.finish_reason,
                    'tool_calls': list(accumulated_tool_calls.values()) if accumulated_tool_calls else None,
                    'model': model_name or self.config.model,
                    'usage': usage_data
                }
        
        # After the stream ends, if we have usage data but haven't yielded finish yet, yield it now
        # This handles the case where usage comes in a final chunk without finish_reason
        if usage_data and model_name:
            self._notify_usage_callbacks(model_name, usage_data, None)
            
            yield {
                'type': 'finish',
                'finish_reason': 'tool_calls',  # We know this was a tool call scenario
                'tool_calls': list(accumulated_tool_calls.values()) if accumulated_tool_calls else None,
                'model': model_name,
                'usage': usage_data
            }
    
    async def _handle_text_based_tool_calling_stream(self, response, tools) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle streaming for models without native function calling support."""
        content_chunks = []
        usage_data = None
        model_name = None
        
        # First, collect all content from the stream
        async for chunk in response:
            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue
                
            delta = choice.delta
            
            # Capture model name and usage data when available
            if hasattr(chunk, 'model') and chunk.model:
                model_name = chunk.model
            if hasattr(chunk, 'usage') and chunk.usage:
                # Handle different usage object formats
                if hasattr(chunk.usage, 'model_dump'):
                    usage_data = chunk.usage.model_dump()
                elif hasattr(chunk.usage, 'dict'):
                    usage_data = chunk.usage.dict()
                else:
                    usage_data = chunk.usage
            
            # Stream text content and collect it
            if hasattr(delta, 'content') and delta.content:
                content_chunks.append(delta.content)
                yield {
                    'type': 'text-delta',
                    'content': delta.content
                }
        
        # After streaming, analyze content for tool calls (if tools are available)
        if tools and content_chunks:
            full_content = ''.join(content_chunks)
            # TODO: Implement text-based tool call detection here
            # This would parse the content for tool usage patterns and emit tool-call chunks
            # For now, just finish the stream
            
        # Notify usage callbacks before yielding finish
        if usage_data and model_name:
            self._notify_usage_callbacks(model_name, usage_data, None)
        
        yield {
            'type': 'finish',
            'finish_reason': 'stop',
            'model': model_name or self.config.model,
            'usage': usage_data
        } 