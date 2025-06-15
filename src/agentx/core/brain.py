"""
Brain Component - LLM Gateway

Handles all LLM interactions for agents, including provider abstraction,
prompt formatting, and response parsing.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel

from ..utils.logger import get_logger
from .config import LLMConfig
from .tool import get_tool_schemas, execute_tool

logger = get_logger(__name__)


class LLMMessage(BaseModel):
    """Standard message format for LLM interactions."""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: Optional[datetime] = None


class LLMResponse(BaseModel):
    """Response from LLM call."""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None
    timestamp: datetime


class Brain:
    """
    Brain component that handles all LLM interactions for an agent.
    
    Provides a unified interface for different LLM providers and handles
    prompt formatting, response parsing, and error handling.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize Brain with LLM configuration.
        
        Args:
            config: LLM configuration including provider, model, etc.
        """
        self.config = config
        self._client = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure LLM client is initialized."""
        if self._initialized:
            return
            
        try:
            # Use litellm for provider abstraction
            import litellm
            
            # Determine provider from config or model name
            provider = getattr(self.config, 'provider', None)
            if not provider and '/' in self.config.model:
                provider = self.config.model.split('/')[0]
            
            # Set API key from config or environment
            api_key = self.config.api_key
            if not api_key and provider:
                # Try to get from environment based on provider
                env_key_map = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY", 
                    "deepseek": "DEEPSEEK_API_KEY",
                    "ollama": "OLLAMA_API_KEY"
                }
                env_key = env_key_map.get(provider.lower())
                if env_key:
                    api_key = os.getenv(env_key)
            
            if not api_key and provider and provider.lower() != "ollama":
                logger.warning(f"No API key found for provider {provider}")
            
            # Configure litellm
            if api_key and provider:
                os.environ[f"{provider.upper()}_API_KEY"] = api_key
                
            if self.config.base_url and provider:
                # Set base URL for custom endpoints
                if provider.lower() == "deepseek":
                    os.environ["DEEPSEEK_API_BASE"] = self.config.base_url
                elif provider.lower() == "openai":
                    os.environ["OPENAI_API_BASE"] = self.config.base_url
                    
            self._initialized = True
            model_display = self.config.model if '/' in self.config.model else f"{provider}/{self.config.model}" if provider else self.config.model
            logger.info(f"Brain initialized with {model_display}")
            
        except ImportError:
            logger.error("litellm package not available. Install with: pip install litellm")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Brain: {e}")
            raise
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        available_tools: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt to prepend
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            available_tools: Optional list of tool names available to the agent
            
        Returns:
            LLM response with content and metadata
        """
        await self._ensure_initialized()
        
        try:
            import litellm
            
            # Format messages for LLM
            formatted_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                # Always append current date/time to system prompt
                current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
                enhanced_system_prompt = f"{system_prompt}\n\nCurrent date and time: {current_datetime}"
                
                formatted_messages.append({
                    "role": "system",
                    "content": enhanced_system_prompt
                })
            
            # Add conversation messages
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare call parameters
            # Handle model name - if it already includes provider prefix, use as-is
            model_name = self.config.model
            if hasattr(self.config, 'provider') and self.config.provider and '/' not in model_name:
                model_name = f"{self.config.provider}/{self.config.model}"
            
            call_params = {
                "model": model_name,
                "messages": formatted_messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "timeout": self.config.timeout
            }
            
            # Add tool schemas if tools are available
            if available_tools:
                tool_schemas = get_tool_schemas(available_tools)
                if tool_schemas:
                    call_params["tools"] = tool_schemas
                    call_params["tool_choice"] = "auto"
            
            # Add base URL if configured
            if self.config.base_url:
                call_params["api_base"] = self.config.base_url
            
            logger.debug(f"Making LLM call with model: {call_params['model']}")
            
            # Make the LLM call
            response = await litellm.acompletion(**call_params)
            
            # Handle tool calls if present
            message = response.choices[0].message
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Execute tool calls and get responses
                tool_responses = []
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = tool_call.function.arguments
                    
                    # Parse arguments if they're a string
                    if isinstance(tool_args, str):
                        import json
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            tool_args = {}
                    
                    # Execute the tool
                    tool_result = await execute_tool(tool_name, **tool_args)
                    
                    # Handle different tool result formats
                    if hasattr(tool_result, 'success'):
                        result_content = tool_result.result if tool_result.success else f"Error: {tool_result.error}"
                    elif isinstance(tool_result, str):
                        result_content = tool_result
                    else:
                        result_content = str(tool_result)
                    
                    tool_responses.append({
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "result": result_content
                    })
                
                # Add tool call message and responses to conversation
                formatted_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in message.tool_calls
                    ]
                })
                
                # Add tool responses
                for tool_response in tool_responses:
                    formatted_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_response["tool_call_id"],
                        "name": tool_response["name"],
                        "content": str(tool_response["result"])
                    })
                
                # Make another call to get the final response
                call_params["messages"] = formatted_messages
                call_params.pop("tools", None)  # Remove tools for final call
                call_params.pop("tool_choice", None)
                
                final_response = await litellm.acompletion(**call_params)
                content = final_response.choices[0].message.content
                usage = final_response.usage.dict() if final_response.usage else None
                finish_reason = final_response.choices[0].finish_reason
            else:
                # No tool calls, use original response
                content = message.content
                usage = response.usage.dict() if response.usage else None
                finish_reason = response.choices[0].finish_reason
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=finish_reason,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            # Return a fallback response for demo purposes
            # Extract provider for error message
            provider = getattr(self.config, 'provider', None)
            if not provider and '/' in self.config.model:
                provider = self.config.model.split('/')[0]
            
            return LLMResponse(
                content=f"I apologize, but I'm having trouble connecting to the {provider or 'LLM'} API. "
                       f"This could be due to missing API keys or network issues. "
                       f"Error: {str(e)}",
                model=self.config.model,
                usage=None,
                finish_reason="error",
                timestamp=datetime.now()
            )
    
    async def stream_response(
        self,
        messages: List[LLMMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Stream response from the LLM in real-time chunks.
        
        This method enables real-time streaming where the LLM response is yielded
        piece by piece as it's generated, rather than waiting for the complete response.
        
        Args:
            messages: List of conversation messages
            system_prompt: Optional system prompt to prepend
            temperature: Override temperature setting
            max_tokens: Override max tokens setting
            
        Yields:
            str: Individual chunks of the response as they arrive from the LLM
            
        Example:
            async for chunk in brain.stream_response(messages):
                print(chunk, end='', flush=True)  # Print each word as it arrives
        """
        await self._ensure_initialized()
        
        try:
            import litellm
            
            # Format messages for LLM
            formatted_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                # Always append current date/time to system prompt
                current_datetime = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
                enhanced_system_prompt = f"{system_prompt}\n\nCurrent date and time: {current_datetime}"
                
                formatted_messages.append({
                    "role": "system", 
                    "content": enhanced_system_prompt
                })
            
            # Add conversation messages
            for msg in messages:
                formatted_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Prepare call parameters
            # Handle model name - if it already includes provider prefix, use as-is
            model_name = self.config.model
            if hasattr(self.config, 'provider') and self.config.provider and '/' not in model_name:
                model_name = f"{self.config.provider}/{self.config.model}"
            
            call_params = {
                "model": model_name,
                "messages": formatted_messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "timeout": self.config.timeout,
                "stream": True
            }
            
            # Add base URL if configured
            if self.config.base_url:
                call_params["api_base"] = self.config.base_url
            
            logger.debug(f"Making streaming LLM call with model: {call_params['model']}")
            
            # Make the streaming LLM call
            response = await litellm.acompletion(**call_params)
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming LLM call failed: {e}")
            # Yield a fallback response
            yield f"I apologize, but I'm having trouble connecting to the {self.config.provider} API. Error: {str(e)}" 