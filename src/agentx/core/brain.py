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


class LLMMessage(BaseModel):
    """Standard message format for LLM interactions."""
    role: str  # "system", "user", "assistant", "tool"
    content: Optional[str] = None
    tool_calls: Optional[List[Any]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # For tool responses
    timestamp: Optional[datetime] = None


class LLMResponse(BaseModel):
    """Response from LLM call, which can be either text content or a request to call tools."""
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
        
    async def _ensure_initialized(self):
        if not self.initialized:
            self.initialized = True
            logger.info(f"LLM client for '{self.config.model}' initialized.")

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
        
        # Add API credentials and base URL
        if self.config.api_key:
            call_params["api_key"] = self.config.api_key
        if self.config.base_url:
            call_params["api_base"] = self.config.base_url
            
        # Add tools if provided
        if tools:
            call_params["tools"] = tools
            call_params["tool_choice"] = "auto"
            
        return call_params

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> LLMResponse:
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
            
            return LLMResponse(
                content=message.content,
                tool_calls=message.tool_calls if hasattr(message, 'tool_calls') else None,
                model=response.model,
                usage=response.usage.dict() if response.usage else None,
                finish_reason=response.choices[0].finish_reason,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return LLMResponse(
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
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from the LLM in real-time chunks.
        
        This is a PURE streaming LLM call - no tool execution or conversation management.
        If tools are provided and the LLM wants to use them, the stream will end and
        the orchestrator should handle tool execution separately.
        
        Args:
            messages: Conversation history
            system_prompt: Optional system prompt  
            temperature: Override temperature
            tools: Available tools for the LLM
            
        Yields:
            str: Chunks of the response as they arrive from the LLM
        """
        await self._ensure_initialized()
        
        formatted_messages = self._format_messages(messages, system_prompt)
        call_params = self._prepare_call_params(formatted_messages, temperature, tools, stream=True)
        
        try:
            logger.debug(f"Making streaming LLM call with {len(formatted_messages)} messages")
            
            response = await litellm.acompletion(**call_params)
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming LLM call failed: {e}")
            yield f"I apologize, but I encountered an error: {str(e)}" 